from sparkle import parsing


def test_native_tool_call_dict_args():
    calls = [{"function": {"name": "update_self", "arguments": {"soul": "calm"}}}]
    assert parsing.extract_tool_call(calls, "") == ("update_self", {"soul": "calm"})


def test_native_tool_call_string_args():
    calls = [{"function": {"name": "update_self", "arguments": '{"soul": "calm"}'}}]
    assert parsing.extract_tool_call(calls, None) == ("update_self", {"soul": "calm"})


def test_fenced_json_block():
    content = 'Sure!\n```json\n{"name": "update_self", "arguments": {"soul": "witty"}}\n```'
    assert parsing.extract_tool_call(None, content) == ("update_self", {"soul": "witty"})


def test_fenced_tool_block():
    content = '```tool\n{"name":"update_self","arguments":{"system":"be terse"}}\n```'
    assert parsing.extract_tool_call(None, content) == ("update_self", {"system": "be terse"})


def test_tool_call_tag():
    content = "<tool_call>{\"name\": \"update_self\", \"arguments\": {\"soul\": \"x\"}}</tool_call>"
    assert parsing.extract_tool_call(None, content) == ("update_self", {"soul": "x"})


def test_bare_brace_in_prose():
    content = 'Okay I will update myself: {"name": "update_self", "arguments": {"soul": "bold"}} done.'
    assert parsing.extract_tool_call(None, content) == ("update_self", {"soul": "bold"})


def test_trailing_comma_repair():
    content = '{"name": "update_self", "arguments": {"soul": "bold",}}'
    assert parsing.extract_tool_call(None, content) == ("update_self", {"soul": "bold"})


def test_single_quote_repair():
    content = "{'name': 'update_self', 'arguments': {'soul': 'bold'}}"
    name, args = parsing.extract_tool_call(None, content)
    assert name == "update_self"
    assert args == {"soul": "bold"}


def test_bare_args_object_no_wrapper():
    content = '{"soul": "a brand new vibe"}'
    assert parsing.extract_tool_call(None, content) == ("update_self", {"soul": "a brand new vibe"})


def test_plain_conversation_no_tool():
    assert parsing.extract_tool_call(None, "Just chatting, nothing to update.") is None
    assert parsing.extract_tool_call([], "Here is some {curly} text") is None


def test_unknown_tool_ignored():
    calls = [{"function": {"name": "delete_everything", "arguments": {}}}]
    assert parsing.extract_tool_call(calls, "") is None


def test_never_raises_on_garbage():
    assert parsing.extract_tool_call(None, '{"name": "update_self", "arguments": {{{') is None
    assert parsing.extract_tool_call("not a list", None) is None
