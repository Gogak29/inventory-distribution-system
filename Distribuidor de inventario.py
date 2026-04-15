import threading
from datetime import date  

stores = {}
inventory = {}
items_distributed = {}

with open('store_inventory_requests.txt', 'r') as f:
    store_requests = f.readlines()
with open('warehouse_inventory.txt', 'r') as f:
    warehouse_inventory = f.readlines()

  
#Parsing of inventory and requests
for line in store_requests:
    if line.startswith('Store:'):
        store = line[7:].strip()
        stores[store] = {}
    elif line.startswith('product:'):
        data = line.split()
        product = data[1]
        quantity = int(data[4])
        # Sum instead of overwrite
        if product in stores[store]:
            stores[store][product] += quantity
        else:
            stores[store][product] = quantity

for line in warehouse_inventory:
    data = line.split()
    product = data[1]
    stock = int(data[3])
    inventory[product] = stock

def print_requests(): #Show petitions from the stores
    print(f"Today requests: {date.today()}:")
    for store, products in stores.items():
        print(f"{store}:")
        for product, request in products.items():
            print(f"- {product}: {request}")
         
def inventory_control(): 
    for product, stock in inventory.items():
        if stock == 0:
            print(f"- {product}: NO STOCK")
        else:
            print(f"- {product}: {stock}")
    while True:
        opt = int(input('Come back [0] | Refill stock [1] | Organize by quantity [2] | Organize by name [3]: '))
        if opt == 0:
            break
        elif opt == 1:
            for product, stock in inventory.items():
                if stock == 0:
                    print(f"- {product}: NO STOCK")
            selected_product = input('Which one do you want to refill?: ')
            if selected_product in inventory:
                inventory[selected_product] += int(input('How many units do you want to add?: '))
                print(f"Stock updated for {selected_product}")
                save_inventory()
            else:
                print('Product not found.')
        elif opt == 2:
            sorted_inventory = sorted(inventory.items(), key=lambda x: x[1], reverse=True)
            for product, stock in sorted_inventory:
                print(f"- {product}: {stock}")
        elif opt == 3:
            sorted_inventory = sorted(inventory.items(), key=lambda x: x[0], reverse=True)
            for product, stock in sorted_inventory:
                print(f"- {product}: {stock}")
            

def save_inventory():
    with open('warehouse_inventory.txt', 'w') as f:
        for product, stock in inventory.items():
            f.write(f"product {product} stock {stock}\n")
            
def save_distribution():
    with open('store_inventory_requests.txt', 'w') as f:
        for store, products in stores.items():
            f.write(f"\nStore: {store}\n")
            for product, quantity in products.items():
                f.write(f"product: {product} , quantity: {quantity}\n")

def manual_distribution(selected_product):
    print('------------------------------------------------------------')
    i = 0
    for store, products in stores.items():
        for product, request in products.items():
            if product == selected_product:
                i += 1
                distribution = int(input(f"{i}) {store} needs: {request} | {product} stock: {inventory[product]} | You distribute: "))
                
                if distribution <= inventory[selected_product] and distribution <= request:
                    
                    if store not in items_distributed:
                        items_distributed[store] = {}
                        if product not in items_distributed[store]:
                            items_distributed[store][product] = 0
                    items_distributed[store][product] += distribution
                    
                    inventory[selected_product] -= distribution
                    stores[store][product] -= distribution
                    print(f"Distributed {distribution} units of {product} to {store}.")
                    save_inventory()
                else:
                    print(f"Cannot distribute {distribution} units. Check stock and request.")

def print_requests_for_product(selected_product, print_stock=True):
    ask = False
    n = 0
    if selected_product not in inventory:
                print('Product not found in inventory.')
                return ask
    if print_stock:
        print(f"{selected_product.capitalize()} in stock: {inventory[selected_product]}")
        for store, products in stores.items():
                for product, request in products.items():
                    if product == selected_product:
                        if request > 0:
                            ask = True
                            n += 1
                            print(f"{n}- {store}: Needs {request} {product}")
                        else:
                            n += 1
                            print(f"{n}- {store}: {product.capitalize()} satisfied")
    for store, products in stores.items():
            for product, request in products.items():
                if product == selected_product:
                    if request > 0:
                        ask = True
    return ask

def manual_distribution_menu(selected_product):
    s_product = selected_product
    ask = print_requests_for_product(s_product, print_stock=True)
    while True:
        ask = print_requests_for_product(s_product, print_stock=False)
        if inventory[s_product] == 0:
            print(f"No stock available for {s_product}.")
            s_product = input('List of products in stock [0] | Distribute another product [write it]: ')
            if s_product == '0':
                    break
            print_requests_for_product(s_product, print_stock=True)
        else:
            if ask == False:
                print(f"All requests for {s_product} have been satisfied.")
                s_product = input('List of products in stock [0] | Distribute another product [write it]: ')
                if s_product == '0':
                    break
                print_requests_for_product(s_product, print_stock=True)
            else:
                manual_distribution(s_product)
                print_requests_for_product(s_product, print_stock=True)
                opt = input('List of products in stock [0] | Distribute more [1]: ')
                if opt == '0':
                    break


def automated_distribution():
    print('no')

def main():
    # Principal Hub
    opt = 0    
    while True:
        opt = input('Exit [0] | Stores requests: [1] | Warehouse inventory: [2] | Manual distribution: [3] | Automated distribution: [4] | Distribuited products: [5] ')
        if opt == '0':
            print('Exiting...')
            break
        
        elif opt == '1':
            print_requests()
        
        elif opt == '2':
            inventory_control()
        
        elif opt == '3':
            opt = '1'
            while True:
                print("Warehouse Inventory:")
                for product, stock in sorted(inventory.items()):
                    print(f"- {product}: {stock}")
                selected_product = input('Main menu [0] | Select product to distribute [write it]: ')
                if selected_product == '0':
                    break
                if selected_product in inventory:
                    if inventory[selected_product] == 0:
                        print('No stock available for this product.')
                    else:
                        manual_distribution_menu(selected_product)
                else:
                    print('Product not found.')
        
        elif opt == '4':
            automated_distribution()
        
        elif opt == '5':
            while True:
                print(f"Products distributed on {date.today()}:")
                if not items_distributed:
                    print("No products have been distributed yet.")
                
                for store, products in items_distributed.items():
                    print(f"{store}:")
                    for product, distribution in products.items():
                        print(f"- {product}: {distribution} units")
                opt = input('Come back [0] | Save distribution [1]')
                if opt == '0':
                    break
                elif opt == '1':
                    save_distribution()
                    items_distributed.clear()
                    print('Distribution saved successfully.')
                else:
                    print('Invalid option. Please try again.')
            

if __name__ == "__main__":
    main()            
   
