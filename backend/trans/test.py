from backend.trans.translation import classify_issue

print("Enter complaints. Type 'exit' to stop.\n")

while True:
    text = input("Issue: ").strip()

    if text.lower() == "exit":
        break

    if not text:
        continue

    try:
        category = classify_issue(text)
        print(f"Category: {category}\n")
    except Exception as e:
        print(f"Error: {e}\n")