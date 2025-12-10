import google.generativeai as genai
try:
    print(f"GenerationConfig has MediaResolution: {hasattr(genai.types.GenerationConfig, 'MediaResolution')}")
    print(dir(genai.types.GenerationConfig))
except Exception as e:
    print(f"Error: {e}")
