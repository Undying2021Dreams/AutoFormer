import xml.etree.ElementTree as ET

from autoformer.mathml import mathml_to_latex

NS = 'xmlns:m="http://www.w3.org/1998/Math/MathML"'


def latex(body: str) -> str:
    root = ET.fromstring(f"<wrap {NS}><m:math>{body}</m:math></wrap>")
    return mathml_to_latex(root[0])


def test_fraction_and_unicode_minus():
    assert latex("<m:mfrac><m:mn>3</m:mn><m:mn>2</m:mn></m:mfrac>"
                 "<m:mo>−</m:mo><m:mn>1</m:mn>") == r"\frac{3}{2}-1"


def test_command_is_not_merged_with_the_next_letter():
    # Was "\pir": an unknown command, and KaTeX refused the expression.
    out = latex("<m:mi>C</m:mi><m:mo>=</m:mo><m:mn>2</m:mn><m:mi>π</m:mi><m:mi>r</m:mi>")
    assert r"\pi r" in out
    assert r"\pir" not in out


def test_underscores_are_a_blank_not_a_subscript():
    # Was "2___4", which LaTeX reads as subscripts and rejects.
    out = latex("<m:mn>2</m:mn><m:mo>___</m:mo><m:mn>4</m:mn>")
    assert out == r"2\underline{\hspace{2em}}4"


def test_combining_slash_is_a_crossed_out_digit():
    assert latex("<m:mn>2̸</m:mn>") == r"\cancel{2}"


def test_math_symbol_inside_text_is_moved_to_maths_mode():
    # KaTeX rejects "\text{≠,}"; the symbol has to sit outside \text.
    out = latex("<m:mtext>≠,</m:mtext>")
    assert out == r"\neq \text{,}"


def test_scripts_and_roots():
    assert latex("<m:msup><m:mi>x</m:mi><m:mn>2</m:mn></m:msup>") == "x^{2}"
    assert latex("<m:msqrt><m:mn>9</m:mn></m:msqrt>") == r"\sqrt{9}"
    assert latex("<m:mroot><m:mn>8</m:mn><m:mn>3</m:mn></m:mroot>") == r"\sqrt[3]{8}"


def test_multi_letter_words_are_upright_but_symbols_are_not():
    assert latex("<m:mi>cm</m:mi>") == r"\mathrm{cm}"
    assert latex("<m:mi>sin</m:mi><m:mi>x</m:mi>") == r"\sin x"


def test_table_becomes_an_array():
    out = latex("<m:mtable><m:mtr><m:mtd><m:mi>a</m:mi></m:mtd><m:mtd><m:mi>b</m:mi></m:mtd></m:mtr>"
                "<m:mtr><m:mtd><m:mi>c</m:mi></m:mtd><m:mtd><m:mi>d</m:mi></m:mtd></m:mtr></m:mtable>")
    assert out == r"\begin{array}{ll}a & b \\ c & d\end{array}"
