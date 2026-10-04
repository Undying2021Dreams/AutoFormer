"""
The corpus rules that matter most, checked on a tiny hand-written module
so the tests run without downloading the books.
"""

from pathlib import Path

from autoformer.corpus import parse_module

MODULE = """<document xmlns="http://cnx.rice.edu/cnxml" xmlns:m="http://www.w3.org/1998/Math/MathML">
<title>Solve Equations</title>
<metadata xmlns:md="http://cnx.rice.edu/mdml">
  <md:abstract><para>By the end:</para>
    <list><item>Verify a solution</item><item>Solve equations</item></list>
  </md:abstract>
</metadata>
<content>
  <para>To solve, isolate the variable.</para>
  <example>
    <exercise><problem><para>Solve <m:math><m:mi>x</m:mi><m:mo>+</m:mo><m:mn>1</m:mn><m:mo>=</m:mo><m:mn>3</m:mn></m:math>.</para></problem>
    <solution><para>Subtract 1. <media alt="x equals 2"><image src="a.png"/></media></para></solution></exercise>
  </example>
  <note class="try"><exercise><problem><para>TRY-PROBLEM</para></problem>
    <solution><para>TRY-ANSWER</para></solution></exercise></note>
  <section class="section-exercises">
    <section class="practice-perfect">
      <exercise><problem><para>PRACTICE-PROBLEM</para></problem>
      <solution><para>PRACTICE-ANSWER</para></solution></exercise>
    </section>
    <section class="writing">
      <exercise><problem><para>WRITING-PROBLEM</para></problem></exercise>
    </section>
  </section>
  <section class="practice-test">
    <exercise><problem><para>TEST-PROBLEM</para></problem></exercise>
  </section>
</content>
</document>"""


def section(tmp_path: Path):
    path = tmp_path / "m1" / "index.cnxml"
    path.parent.mkdir()
    path.write_text(MODULE)
    return parse_module(path, book="b", chapter=1, chapter_title="c", position=0)


def test_worked_examples_stay_in_the_teaching_text(tmp_path):
    # They were once dropped, leaving the books without their examples.
    s = section(tmp_path)
    assert "**Example**" in s.text
    assert "$x+1=3$" in s.text
    assert "Subtract 1." in s.text


def test_step_images_are_replaced_by_their_alt_text(tmp_path):
    assert "[image: x equals 2]" in section(tmp_path).text


def test_no_exercise_leaks_into_the_teaching_text(tmp_path):
    text = section(tmp_path).text
    for marker in ("TRY", "PRACTICE", "WRITING", "TEST"):
        assert marker not in text


def test_worked_examples_are_not_reference_exercises(tmp_path):
    problems = [e.problem for e in section(tmp_path).exercises]
    assert not any("x+1=3" in p for p in problems)


def test_exercise_kinds_come_from_the_innermost_container(tmp_path):
    kinds = {e.problem: e.kind for e in section(tmp_path).exercises}
    assert kinds == {
        "TRY-PROBLEM": "try",
        "PRACTICE-PROBLEM": "practice",
        "WRITING-PROBLEM": "writing",
        "TEST-PROBLEM": "practice-test",
    }


def test_missing_answers_are_none_not_empty(tmp_path):
    answers = {e.kind: e.solution for e in section(tmp_path).exercises}
    assert answers["practice"] == "PRACTICE-ANSWER"
    assert answers["writing"] is None


def test_objectives_are_extracted_cleanly(tmp_path):
    assert section(tmp_path).objectives == ["Verify a solution", "Solve equations"]
