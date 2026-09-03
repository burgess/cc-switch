from pathlib import Path

p = Path("src-tauri/src/proxy/usage/parser.rs")
s = p.read_text()

old = '''                            // 从 message_delta 中处理缓存命中(cache_read_input_tokens)
                            if delta_input.unwrap_or(0) == 0 && usage.cache_read_tokens == 0 {
                                if let Some(cache_read) = delta_cache_read {
                                    usage.cache_read_tokens = cache_read;
                                }
                            }
                            // 从 message_delta 中处理缓存创建(cache_creation_input_tokens)
                            // 注: 现在 zhipu 没有返回 cache_creation_input_tokens 字段
                            if delta_input.unwrap_or(0) == 0 && usage.cache_creation_tokens == 0 {
                                if let Some(cache_creation) = delta_cache_creation {
                                    usage.cache_creation_tokens = cache_creation;
                                }
                            }
'''
new = '''                            let allow_cache_fallback = delta_input.is_none()
                                || (start_input_tokens == 0 && delta_input == Some(0));
                            // 从 message_delta 中处理缓存命中(cache_read_input_tokens)
                            if allow_cache_fallback && usage.cache_read_tokens == 0 {
                                if let Some(cache_read) = delta_cache_read {
                                    usage.cache_read_tokens = cache_read;
                                }
                            }
                            // 从 message_delta 中处理缓存创建(cache_creation_input_tokens)
                            // 注: 现在 zhipu 没有返回 cache_creation_input_tokens 字段
                            if allow_cache_fallback && usage.cache_creation_tokens == 0 {
                                if let Some(cache_creation) = delta_cache_creation {
                                    usage.cache_creation_tokens = cache_creation;
                                }
                            }
'''
if old not in s:
    raise SystemExit("fallback block not found")
s = s.replace(old, new, 1)

marker = '''    #[test]
    fn test_claude_stream_accepts_coherent_zero_input_correction() {
'''
test = '''    #[test]
    fn test_claude_stream_rejects_incoherent_zero_input_cache_tuple() {
        let events = vec![
            json!({
                "type": "message_start",
                "message": {
                    "model": "claude-sonnet-4-20250514",
                    "usage": {
                        "input_tokens": 200_000,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0
                    }
                }
            }),
            json!({
                "type": "message_delta",
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_input_tokens": 100_000
                }
            }),
        ];

        let usage = TokenUsage::from_claude_stream_events(&events).unwrap();
        assert_eq!(usage.input_tokens, 200_000);
        assert_eq!(usage.output_tokens, 0);
        assert_eq!(usage.cache_read_tokens, 0);
        assert_eq!(usage.cache_creation_tokens, 0);
        assert_eq!(
            usage.model,
            Some("claude-sonnet-4-20250514".to_string())
        );
    }

'''
if marker not in s:
    raise SystemExit("test marker not found")
s = s.replace(marker, test + marker, 1)
p.write_text(s)
