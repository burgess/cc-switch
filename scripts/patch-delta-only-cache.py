from pathlib import Path

p = Path("src-tauri/src/proxy/usage/parser.rs")
s = p.read_text()

old = '''                                if should_use_delta_input {
                                    usage.input_tokens = input;
                                    usage.cache_read_tokens = delta_cache_read.unwrap_or(0);
                                    usage.cache_creation_tokens = delta_cache_creation.unwrap_or(0);
                                }
'''
new = '''                                if should_use_delta_input {
                                    usage.input_tokens = input;
                                    if start_input_tokens == 0 {
                                        if let Some(cache_read) = delta_cache_read {
                                            usage.cache_read_tokens = cache_read;
                                        }
                                        if let Some(cache_creation) = delta_cache_creation {
                                            usage.cache_creation_tokens = cache_creation;
                                        }
                                    } else {
                                        usage.cache_read_tokens = delta_cache_read.unwrap_or(0);
                                        usage.cache_creation_tokens =
                                            delta_cache_creation.unwrap_or(0);
                                    }
                                }
'''
if old not in s:
    raise SystemExit("accepted delta block not found")
s = s.replace(old, new, 1)

marker = '''    #[test]
    fn test_claude_stream_updates_delta_only_usage_from_later_delta() {
'''
test = '''    #[test]
    fn test_claude_stream_delta_only_preserves_omitted_cache_bucket() {
        let events = vec![
            json!({
                "type": "message_start",
                "message": {
                    "model": "qwen-max",
                    "usage": {
                        "input_tokens": 0,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0
                    }
                }
            }),
            json!({
                "type": "message_delta",
                "usage": {
                    "input_tokens": 90_000,
                    "output_tokens": 100,
                    "cache_read_input_tokens": 110_000
                }
            }),
            json!({
                "type": "message_delta",
                "usage": {
                    "input_tokens": 80_000,
                    "output_tokens": 1_000
                }
            }),
        ];

        let usage = TokenUsage::from_claude_stream_events(&events).unwrap();
        assert_eq!(usage.input_tokens, 80_000);
        assert_eq!(usage.output_tokens, 1_000);
        assert_eq!(usage.cache_read_tokens, 110_000);
        assert_eq!(usage.cache_creation_tokens, 0);
        assert_eq!(usage.model, Some("qwen-max".to_string()));
    }

'''
if marker not in s:
    raise SystemExit("delta-only test marker not found")
s = s.replace(marker, test + marker, 1)

p.write_text(s)
