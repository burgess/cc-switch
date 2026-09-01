from pathlib import Path

p = Path("src-tauri/src/proxy/usage/parser.rs")
s = p.read_text()

old = '''                                let corrected_cache_tuple = has_delta_cache
                                    && start_input_tokens > 0
                                    && input < start_input_tokens
                                    && (fresh_plus_cache_read == Some(start_input_tokens)
                                        || fresh_plus_all_cache == Some(start_input_tokens));
'''
new = '''                                let corrected_cache_tuple = has_delta_cache
                                    && start_input_tokens > 0
                                    && input < start_input_tokens
                                    && match delta_cache_creation {
                                        Some(cache_creation) if cache_creation > 0 => {
                                            fresh_plus_all_cache == Some(start_input_tokens)
                                        }
                                        _ => fresh_plus_cache_read == Some(start_input_tokens),
                                    };
'''
if old not in s:
    raise SystemExit("corrected tuple block not found")
s = s.replace(old, new, 1)

marker = '''    #[test]
    fn test_claude_stream_rejects_incoherent_later_delta_after_correction() {
'''
regression = '''    #[test]
    fn test_claude_stream_rejects_overfull_tuple_with_cache_creation() {
        let events = vec![
            json!({
                "type": "message_start",
                "message": {
                    "model": "qwen-max",
                    "usage": {
                        "input_tokens": 200_000,
                        "cache_read_input_tokens": 180_000,
                        "cache_creation_input_tokens": 2_000
                    }
                }
            }),
            json!({
                "type": "message_delta",
                "usage": {
                    "input_tokens": 80_000,
                    "output_tokens": 1_000,
                    "cache_read_input_tokens": 120_000,
                    "cache_creation_input_tokens": 10_000
                }
            }),
        ];

        let usage = TokenUsage::from_claude_stream_events(&events).unwrap();
        assert_eq!(usage.input_tokens, 200_000);
        assert_eq!(usage.output_tokens, 1_000);
        assert_eq!(usage.cache_read_tokens, 180_000);
        assert_eq!(usage.cache_creation_tokens, 2_000);
        assert_eq!(usage.model, Some("qwen-max".to_string()));
    }

'''
if marker not in s:
    raise SystemExit("test insertion marker not found")
s = s.replace(marker, regression + marker, 1)
p.write_text(s)
