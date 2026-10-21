from deep_translator import GoogleTranslator, MyMemoryTranslator

text = "Hello, how are you?"

try:
    result = GoogleTranslator(source="en", target="bn").translate(text)
    print("Google:", result)
except Exception as e:
    print("Google failed, trying MyMemory...")
    result = MyMemoryTranslator(source="english", target="bengali").translate(text)
    print("MyMemory:", result)