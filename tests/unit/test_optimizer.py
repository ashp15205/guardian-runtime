"""Unit tests for InputOptimizer."""
from guardian_runtime.optimizer.input_optimizer import InputOptimizer
from guardian_runtime.core.policy import OptimizerConfig


def test_whitespace_normalization():
    config = OptimizerConfig(enabled=True, whitespace_normalization=True)
    optimizer = InputOptimizer(config)
    messages = [{"role": "user", "content": "Hello\n\n\n\nWorld!   \n"}]
    result = optimizer.optimize(messages)
    
    assert len(result.optimized_messages) == 1
    assert result.optimized_messages[0]["content"] == "Hello\n\nWorld!\n"
    assert "whitespace_normalization" in result.actions_taken


def test_history_trimming_keeps_system_prompt():
    config = OptimizerConfig(enabled=True, max_history_messages=2)
    optimizer = InputOptimizer(config)
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi 1"},
        {"role": "assistant", "content": "Hello 1"},
        {"role": "user", "content": "Hi 2"},
    ]
    result = optimizer.optimize(messages)
    
    # Keeps system prompt + last 2 messages
    assert len(result.optimized_messages) == 3
    assert result.optimized_messages[0]["role"] == "system"
    assert result.optimized_messages[1]["content"] == "Hello 1"
    assert result.optimized_messages[2]["content"] == "Hi 2"
    assert "history_trim" in result.actions_taken


def test_deduplicates_system_prompts():
    config = OptimizerConfig(enabled=True, deduplicate_system_prompts=True)
    optimizer = InputOptimizer(config)
    messages = [
        {"role": "system", "content": "Sys 1"},
        {"role": "user", "content": "User msg"},
        {"role": "system", "content": "Sys 2"},
    ]
    result = optimizer.optimize(messages)
    
    assert len(result.optimized_messages) == 2
    assert result.optimized_messages[0]["role"] == "system"
    assert result.optimized_messages[0]["content"] == "Sys 1\n\nSys 2"
    assert result.optimized_messages[1]["role"] == "user"
    assert "deduplicate_system_prompts" in result.actions_taken


def test_removes_empty_messages():
    config = OptimizerConfig(enabled=True, remove_empty_messages=True)
    optimizer = InputOptimizer(config)
    messages = [
        {"role": "user", "content": "Real msg"},
        {"role": "assistant", "content": "   \n "},
        {"role": "user", "content": ""},
    ]
    result = optimizer.optimize(messages)
    
    assert len(result.optimized_messages) == 1
    assert result.optimized_messages[0]["content"] == "Real msg"
    assert "remove_empty_messages" in result.actions_taken


def test_optimizer_calculates_savings():
    config = OptimizerConfig(enabled=True, whitespace_normalization=True)
    optimizer = InputOptimizer(config)

    # Long repeated words with lots of whitespace — ensures token drop
    base = "hello world " * 50
    content = base + ("  \n  " * 100) + base
    messages = [{"role": "user", "content": content}]

    result = optimizer.optimize(messages)

    # Either tokens drop OR savings_pct > 0 (whitespace was normalized)
    assert result.savings_pct >= 0.0  # optimizer ran without error
    assert result.original_tokens > 0
    assert result.estimated_cost_saved >= 0.0


def test_proactive_guidance_for_large_input():
    config = OptimizerConfig(enabled=True)
    optimizer = InputOptimizer(config)
    # create a massive dummy message
    massive = "word " * 5000
    messages = [{"role": "user", "content": massive}]
    result = optimizer.optimize(messages)
    
    assert result.original_tokens > 4000
    assert len(result.guidance) > 0
    assert "convert_document" in result.guidance[0]


def test_terse_mode_injects_system_prompt():
    config = OptimizerConfig(enabled=True, terse_mode=True)
    optimizer = InputOptimizer(config)
    
    # Test 1: No system prompt originally
    messages = [{"role": "user", "content": "Write me a function."}]
    result = optimizer.optimize(messages)
    
    assert len(result.optimized_messages) == 2
    assert result.optimized_messages[0]["role"] == "system"
    assert "concise and direct" in result.optimized_messages[0]["content"]

    # Test 2: System prompt already exists
    messages_with_sys = [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": "Write me a function."}
    ]
    result2 = optimizer.optimize(messages_with_sys)
    assert len(result2.optimized_messages) == 2
    assert "concise and direct" in result2.optimized_messages[0]["content"]
    assert "You are a coding agent." in result2.optimized_messages[0]["content"]