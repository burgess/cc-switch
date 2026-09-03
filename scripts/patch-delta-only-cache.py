from pathlib import Path

p = Path("src-tauri/src/proxy/usage/parser.rs")
s = p.read_text()

old = '''                                let delta_only_input = start_input_tokens == 0
                                    && input > 0
                                    && (!input_from_delta || input <= usage.input_tokens);
                                let should_use_delta_input =
                                    delta_only_input || corrected_cache_tuple;
'''
new = '''                                let delta_only_has_cache = delta_cache_read.unwrap_or(0) > 0
                                    || delta_cache_creation.unwrap_or(0) > 0;
                                let delta_only_input = start_input_tokens == 0
                                    && ((input > 0
                                        && (!input_from_delta || input <= usage.input_tokens))
                                        || (input == 0 && delta_only_has_cache));
                                let should_use_delta_input =
                                    delta_only_input || corrected_cache_tuple;
'''
if old not in s:
    raise SystemExit("delta-only acceptance block not found")
s = s.replace(old, new, 1)

marker = '''    #[test]
    fn test_claude_stream_delta_only_rejects_larger_later_input() {
'''
test = '''    #[test]
    fn test_claude_stream_delta_only_accepts_final_zero_input_cache_correction() {
        let events = vec![
            json!({
                "type": "message_start",
                "message": {
                    "model": "qwen-max",
                    "usage": {"input_tokens": 0}
                }
            }),
            json!({
                "type": "message_delta",
                "usage": {
                    "input_tokens": 80,
                    "output_tokens": 100,
                    "cache_read_input_tokens": 120
                }
            }),
            json!({
                "type": "message_delta",
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 1_000,
                    "cache_read_input_tokens": 200
                }
            }),
        ];

        let usage = TokenUsage::from_claude_stream_events(&events).unwrap();
        assert_eq!(usage.input_tokens, 0);
        assert_eq!(usage.output_tokens, 1_000);
        assert_eq!(usage.cache_read_tokens, 200);
        assert_eq!(usage.cache_creation_tokens, 0);
    }

'''
if marker not in s:
    raise SystemExit("test marker not found")
s = s.replace(marker, test + marker, 1)

p.write_text(s)
