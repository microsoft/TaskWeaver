def test_handle_delimiter():
    from taskweaver.module.prompt_util import PromptUtil

    text = "This is a test sentence."
    delimiter = ("{{DELIMITER_START_TEMPORAL}}", "{{DELIMITER_END_TEMPORAL}}")
    wrapped_text = PromptUtil.wrap_text_with_delimiter(text, delimiter)
    assert wrapped_text == "{{DELIMITER_START_TEMPORAL}}This is a test sentence.{{DELIMITER_END_TEMPORAL}}"

    assert text == PromptUtil.remove_delimiter(wrapped_text, delimiter)
    assert PromptUtil.remove_parts(wrapped_text, delimiter) == ""

    text = (
        "This is a test sentence. "
        "{{DELIMITER_START_TEMPORAL}}This is a temporal part.{{DELIMITER_END_TEMPORAL}} "
        "This is another test sentence."
    )
    assert PromptUtil.remove_parts(text, delimiter) == "This is a test sentence.  This is another test sentence."
    assert PromptUtil.remove_delimiter(text, delimiter) == (
        "This is a test sentence. " "This is a temporal part. " "This is another test sentence."
    )

    text = "This is a test sentence."
    wrapped_text = PromptUtil.wrap_text_with_delimiter(text, PromptUtil.DELIMITER_TEMPORAL)
    assert wrapped_text == "{{DELIMITER_START_TEMPORAL}}This is a test sentence.{{DELIMITER_END_TEMPORAL}}"
    assert text == PromptUtil.remove_all_delimiters(wrapped_text)

    unmatched_text = "This is a test sentence. {{DELIMITER_START_TEMPORAL}}This is a temporal part."
    assert PromptUtil.remove_all_delimiters(unmatched_text) == "This is a test sentence. This is a temporal part."
    assert PromptUtil.remove_parts(unmatched_text, delimiter) == unmatched_text
