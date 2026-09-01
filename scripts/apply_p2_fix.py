from pathlib import Path

# One-off script executed by the temporary workflow.
p = Path("src-tauri/src/proxy/usage/parser.rs")
s = p.read_text()

old_state = "        let mut input_from_delta = false;\n"
new_state = "        let mut start_input_tokens = 0u32;\n"
if old_state not in s:
    raise SystemExit("input state marker not found")
s = s.replace(old_state, new_state, 1)

old_start = """                            if let Some(input) =
                                msg_usage.get(\"input_tokens\").and_then(|v| v.as_u64())
                            {
                                usage.input_tokens = input as u32;
                            }
"""
new_start = """                            if let Some(input) =
                                msg_usage.get(\"input_tokens\").and_then(|v| v.as_u64())
                            {
                                usage.input_tokens = input as u32;
                                start_input_tokens = input as u32;
                            }
"""
if old_start not in s:
    raise SystemExit("message_start block not found")
s = s.replace(old_start, new_start, 1)

old_logic = """                                let corrected_cache_tuple = has_delta_cache
                                    && input < usage.input_tokens
                                    && (fresh_plus_cache_read == Some(usage.input_tokens)
                                        || fresh_plus_all_cache == Some(usage.input_tokens));

                                let should_use_delta_input = input > 0
                                    && (usage.input_tokens == 0
                                        || input_from_delta
                                        || corrected_cache_tuple);

                                if should_use_delta_input {
                                    usage.input_tokens = input;
                                    input_from_delta = true;
"""
new_logic = """                                let corrected_cache_tuple = has_delta_cache
                                    && start_input_tokens > 0
                                    && input < start_input_tokens
                                    && (fresh_plus_cache_read == Some(start_input_tokens)
                                        || fresh_plus_all_cache == Some(start_input_tokens));

                                let should_use_delta_input = input > 0
                                    && (start_input_tokens == 0 || corrected_cache_tuple);

                                if should_use_delta_input {
                                    usage.input_tokens = input;
"""
if old_logic not in s:
    raise SystemExit("delta selection block not found")
s = s.replace(old_logic, new_logic, 1)

marker = """    #[test]
    fn test_claude_stream_updates_delta_only_usage_from_later_delta() {
"""
regression = """    #[test]
    fn test_claude_stream_rejects_incoherent_later_delta_after_correction() {
        let events = vec![
            json!({
                \"type\": \"message_start\",
                \"message\": {
                    \"model\": \"qwen-max\",
                    \"usage\": {
                        \"input_tokens\": 200_000,
                        \"cache_read_input_tokens\": 180_000,
                        \"cache_creation_input_tokens\": 2_000
                    }
                }
            }),
            json!({
                \"type\": \"message_delta\",
                \"usage\": {
                    \"input_tokens\": 80_000,
                    \"output_tokens\": 100,
                    \"cache_read_input_tokens\": 120_000,
                    \"cache_creation_input_tokens\": 500
                }
            }),
            json!({
                \"type\": \"message_delta\",
                \"usage\": {
                    \"input_tokens\": 200_000,
                    \"output_tokens\": 1_000,
                    \"cache_read_input_tokens\": 120_000,
                    \"cache_creation_input_tokens\": 500
                }
            }),
        ];

        let usage = TokenUsage::from_claude_stream_events(&events).unwrap();
        assert_eq!(usage.input_tokens, 80_000);
        assert_eq!(usage.output_tokens, 1_000);
        assert_eq!(usage.cache_read_tokens, 120_000);
        assert_eq!(usage.cache_creation_tokens, 500);
        assert_eq!(usage.model, Some(\"qwen-max\".to_string()));
    }

"""
if marker not in s:
    raise SystemExit("test insertion marker not found")
s = s.replace(marker, regression + marker, 1)

p.write_text(s)
