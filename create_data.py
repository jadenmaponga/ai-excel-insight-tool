import pandas as pd

data = {
    "date": ["2026-03-01","2026-03-02","2026-03-03","2026-03-04"],
    "product": ["Widget","Widget","Gadget","Gadget"],
    "units": [10,7,12,5],
    "price": [19.99,19.99,29.5,29.5]
}

df = pd.DataFrame(data)

df.to_excel("sales.xlsx", index=False)

print("Dataset created successfully!")