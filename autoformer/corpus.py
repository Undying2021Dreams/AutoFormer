"""
OpenStax CNXML -> a corpus of sections and exercises.

Two outputs, kept apart on purpose:

- sections: the teaching text a question generator is given
- exercises: the book's own questions, used as a reference to judge
  generated questions against

The generator must never see the exercises. If it did, comparing its
questions with the book's would measure copying, not generation.
"""

from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET

from .mathml import M, mathml_to_latex

C = "{http://cnx.rice.edu/cnxml}"
COL = "{http://cnx.rice.edu/collxml}"
MD = "{http://cnx.rice.edu/mdml}"

# Where an exercise sits decides what kind it is. Containers nest, and the
# innermost class wins: a "writing" block inside "section-exercises" is
# writing, not practice.
EXERCISE_KINDS = {
    "section-exercises": "practice",  # untitled drill blocks ("Mixed Practice")
    "practice-perfect": "practice",   # drill, usually checkable by computer
    "everyday": "everyday",           # word problems
    "writing": "writing",             # "explain why", marked against a rubric
    "try": "try",                     # follows a worked example
    "be-prepared": "be-prepared",     # readiness check on earlier sections
    # These two cover a whole chapter, though they sit in its last section.
    "review-exercises": "review",
    "practice-test": "practice-test", # the authors' own end-of-chapter exam
}

# Containers left out of the teaching text, because they hold exercises.
EXERCISE_CONTAINERS = {"section-exercises", "practice-perfect", "everyday",
                       "writing", "try", "be-prepared", "chapter-review",
                       "practice-test", "review-exercises"}


@dataclass
class Exercise:
    book: str
    chapter: int
    section_id: str
    exercise_id: str
    kind: str
    problem: str
    solution: str | None


@dataclass
class Section:
    book: str
    chapter: int
    chapter_title: str
    position: int
    section_id: str
    title: str
    objectives: list[str]
    text: str
    exercises: list[Exercise] = field(default_factory=list)


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def to_text(el: ET.Element) -> str:
    """Render a CNXML element as Markdown-ish text with $LaTeX$ maths."""
    out: list[str] = []
    _render(el, out)
    text = "".join(out)
    lines = [" ".join(line.split()) for line in text.split("\n")]
    # Collapse runs of blank lines left by nested blocks.
    result, blank = [], False
    for line in lines:
        if line:
            result.append(line)
            blank = False
        elif not blank and result:
            result.append("")
            blank = True
    return "\n".join(result).strip()


def _render(el: ET.Element, out: list[str]) -> None:
    if el.tag == M + "math":
        latex = mathml_to_latex(el)
        out.append(f" $${latex}$$ " if el.get("display") == "block" else f" ${latex}$ ")
        out.append(el.tail or "")
        return

    tag = _local(el.tag)

    if tag == "metadata":
        out.append(el.tail or "")
        return

    # The working in worked examples is drawn as images, one per step.
    # Their alt text describes each step in words and matches the image,
    # so it stands in for it: without it a worked example is just the
    # question and the conclusion, with the method missing.
    if tag == "media":
        alt = " ".join((el.get("alt") or "").split())
        out.append(f" [image: {alt}] " if alt else " [image] ")
        out.append(el.tail or "")
        return

    block = tag in ("para", "title", "list", "item", "table", "row",
                    "equation", "example", "note", "solution", "problem")
    if block:
        out.append("\n")
    if tag == "item":
        out.append("- ")
    if tag == "example":
        out.append("**Example**\n")
    if tag == "title":
        out.append("**")
    if tag == "emphasis":
        out.append("**" if el.get("effect") == "bold" else "*")

    out.append(el.text or "")
    for child in el:
        _render(child, out)

    if tag == "emphasis":
        out.append("**" if el.get("effect") == "bold" else "*")
    if tag == "title":
        out.append("**")
    if tag == "newline":
        out.append("\n")
    if tag == "entry":
        out.append(" | ")
    if block:
        out.append("\n")
    out.append(el.tail or "")


def _teaching_text(content: ET.Element) -> str:
    """Everything except the exercise containers."""
    kept = ET.Element("content")
    for child in content:
        cls = set((child.get("class") or "").split())
        if cls & EXERCISE_CONTAINERS:
            continue
        kept.append(_without_exercises(child))
    return to_text(kept)


def _without_exercises(el: ET.Element, in_example: bool = False) -> ET.Element:
    """
    Drop exercises, but keep the ones inside worked examples.

    A worked example is marked up as an exercise with its solution, but it
    is teaching, not testing: it is how a maths book shows the method.
    Dropping it would hand the generator the book without its examples.
    """
    copy = ET.Element(el.tag, el.attrib)
    copy.text, copy.tail = el.text, el.tail
    in_example = in_example or _local(el.tag) == "example"
    for child in el:
        cls = set((child.get("class") or "").split())
        if cls & EXERCISE_CONTAINERS:
            continue
        if _local(child.tag) == "exercise" and not in_example:
            continue
        copy.append(_without_exercises(child, in_example))
    return copy


def _exercises(content: ET.Element, book: str, chapter: int,
               section_id: str) -> list[Exercise]:
    found: list[Exercise] = []

    def walk(el: ET.Element, kind: str | None) -> None:
        # Worked examples are part of the teaching text the generator
        # sees, so they can't also be used to judge it.
        if _local(el.tag) == "example":
            return
        for cls in (el.get("class") or "").split():
            if cls in EXERCISE_KINDS:
                kind = EXERCISE_KINDS[cls]
        if _local(el.tag) == "exercise":
            problem = el.find(C + "problem")
            solution = el.find(C + "solution")
            if problem is not None:
                found.append(Exercise(
                    book=book, chapter=chapter, section_id=section_id,
                    exercise_id=el.get("id", ""),
                    kind=kind or "other",
                    problem=to_text(problem),
                    solution=to_text(solution) if solution is not None else None,
                ))
            return
        for child in el:
            walk(child, kind)

    walk(content, None)
    return found


def parse_module(path: Path, book: str, chapter: int, chapter_title: str,
                 position: int) -> Section:
    root = ET.parse(path).getroot()
    section_id = path.parent.name
    title = root.findtext(C + "title", default="").strip()

    objectives = []
    abstract = root.find(f"{C}metadata/{MD}abstract")
    if abstract is not None:
        objectives = [to_text(item).removeprefix("- ")
                      for item in abstract.iter(C + "item")]

    content = root.find(C + "content")
    section = Section(
        book=book, chapter=chapter, chapter_title=chapter_title,
        position=position, section_id=section_id, title=title,
        objectives=objectives, text=_teaching_text(content),
    )
    section.exercises = _exercises(content, book, chapter, section_id)
    return section


def parse_book(bundle: Path, collection: str) -> list[Section]:
    root = ET.parse(bundle / "collections" / collection).getroot()
    book = root.findtext(f"{COL}metadata/{MD}slug") or collection.split(".")[0]
    sections: list[Section] = []

    chapters = root.find(COL + "content").findall(COL + "subcollection")
    for chapter_no, chapter in enumerate(chapters, start=1):
        chapter_title = chapter.findtext(MD + "title", default="").strip()
        modules = chapter.find(COL + "content").findall(COL + "module")
        for position, module in enumerate(modules):
            doc = bundle / "modules" / module.get("document") / "index.cnxml"
            sections.append(parse_module(doc, book, chapter_no, chapter_title, position))
    return sections
