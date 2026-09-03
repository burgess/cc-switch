from pathlib import Path

p = Path("src-tauri/src/proxy/usage/parser.rs")
s = p.read_text()

old_state = '''        let mut start_input_tokens = 0u32;
'''
new_state = '''        let mut start_input_tokens = 0u32;
        let mut input_from_delta = false;
        let mut corrected_usage_accepted = false;
'''
if old_state not in s:
    raise SystemExit("state marker not found")
s = s.replace(old_state, new_state, 1)

old_accept = '''                                let should_use_delta_input =
                                    (start_input_tokens == 0 && input > 0) || corrected_cache_tuple;

                                if should_use_delta_input {
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
new_accept = '''                                let delta_only_input = start_input_tokens == 0
                                    && input > 0
                                    && (!input_from_delta || input <= usage.input_tokens);
                                let should_use_delta_input = delta_only_input || corrected_cache_tuple;

                                if should_use_delta_input {
                                    usage.input_tokens = input;
                                    if start_input_tokens == 0 {
                                        input_from_delta = true;
                                        if let Some(cache_read) = delta_cache_read {
                                            usage.cache_read_tokens = cache_read;
                                        }
                                        if let Some(cache_creation) = delta_cache_creation {
                                            usage.cache_creation_tokens = cache_creation;
                                        }
                                    } else {
                                        corrected_usage_accepted = true;
                                        usage.cache_read_tokens = delta_cache_read.unwrap_or(0);
                                        usage.cache_creation_tokens =
                                            delta_cache_creation.unwrap_or(0);
                                    }
                                }
'''
if old_accept not in s:
    raise SystemExit("acceptance block not found")
s = s.replace(old_accept, new_accept, 1)

old_fallback = '''                            let allow_cache_fallback = delta_input.is_none()
                                || (start_input_tokens == 0 && delta_input == Some(0));
'''
new_fallback = '''                            let allow_cache_fallback = !corrected_usage_accepted
                                && (delta_input.is_none()
                                    || (start_input_tokens == 0 && delta_input == Some(0)));
'''
if old_fallback not in s:
    raise SystemExit("fallback block not found")
s = s.replace(old_fallback, new_fallback, 1)

marker = '''    #[test]
    fn test_claude_stream_delta_only_preserves_omitted_cache_bucket() {
'''
tests = '''    #[test]
    fn test_claude_stream_delta_only_rejects_larger_later_input() {
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
                    "input_tokens": 200,
                    "output_tokens": 1_000
                }
            }),
        ];

        let usage = TokenUsage::from_claude_stream_events(&events).unwrap();
        assert_eq!(usage.input_tokens, 80);
        assert_eq!(usage.output_tokens, 1_000);
        assert_eq!(usage.cache_read_tokens, 120);
    }

    #[test]
    fn test_claude_stream_rejects_cache_only_delta_after_correction() {
        let events = vec![
            json!({
                "type": "message_start",
                "message": {
                    "model": "qwen-max",
                    "usage": {
                        "input_tokens": 200,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0
                    }
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
                    "output_tokens": 1_000,
                    "cache_creation_input_tokens": 10
                }
            }),
        ];

        let usage = TokenUsage::from_claude_stream_events(&events).unwrap();
        assert_eq!(usage.input_tokens, 80);
        assert_eq!(usage.output_tokens, 1_000);
        assert_eq!(usage.cache_read_tokens, 120);
        assert_eq!(usage.cache_creation_tokens, 0);
    }

'''
if marker not in s:
    raise SystemExit("test marker not found")
s = s.replace(marker, tests + marker, 1)

p.write_text(s)
