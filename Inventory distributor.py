import threading
from datetime import date
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

stores = {}
inventory = {}
items_distributed = {}
store_sellsratio = {}
inventory_days_remaining = {}




# Parsing of inventory and requests
def parse_data():
    with open('stores_inventory_stock.txt', 'r') as f:
        store_stock = f.readlines()
    with open('warehouse_inventory.txt', 'r') as f:
        warehouse_inventory = f.readlines()
    
    stores.clear()
    store_sellsratio.clear()
    inventory.clear()

    store = None
    for line in store_stock:
        if line.startswith('Store:'):
            store = line.split(':')[1].strip()
            stores[store] = {}
        elif line.startswith('product:') and store:
            parts = line.split(',')
            product = parts[0].split(':')[1].strip()
            quantity = int(parts[1].split(':')[1].strip())
            sells_per_day = float(parts[2].split(':')[1].strip())
            stores[store][product] = {
                'quantity': quantity,
                'sells_per_day': sells_per_day
            }
    
    # Calculate average sells per day for each store from the sum of every product sells per day divided by the number of different products
    for store, products in stores.items():
        different_products = float(len(stores[store]))
        store_sellsratio[store] = 0.0
        for product, data in products.items():
            store_sellsratio[store] += data['sells_per_day']
        if different_products > 0.0:
            store_sellsratio[store] /= different_products

    for line in warehouse_inventory:
        data = line.split()
        product = data[1]
        stock = int(data[3])
        inventory[product] = {
            'stock': stock,
            'daysremaining': 0.0,
        }
    
    inventory_daysRemaining()
    
    
def inventory_daysRemaining():
    inventory_days_remaining.clear()
    for product, data in inventory.items():
        inventory_days_remaining[product] = 0.0
        for store, products in stores.items():
            if product in products:
                for inproduct, data in products.items():
                    if inproduct == product:
                        inventory_days_remaining[product] += data['sells_per_day']
        try:
            inventory[product]['daysremaining'] = round(inventory[product]['stock'] / inventory_days_remaining[product])
        except ZeroDivisionError:
            inventory[product]['daysremaining'] = '-'
                
                    
parse_data()


def stock_level_color(quantity):
    if quantity < 70:
        return f"[bold red]{quantity}[/bold red]"
    elif quantity < 130:
        return f"[yellow]{quantity}[/yellow]"
    else:
        return f"[green]{quantity}[/green]"


def days_remaining_color(days, quantity=None, spd=None):
    if quantity is not None and spd is not None:
        try:
            days = quantity / spd if spd > 0 else None
        except ZeroDivisionError:
            days = None

    days = round(days, 1)
    if days < 4:
        return f"[bold red] URGENT!:[/bold red] [red]{days} days remaining[/red]"
    elif days < 6:
        return f"[bold yellow] Low stock:[/bold yellow] [yellow]{days} days remaining[/yellow]"
    elif days >= 6:
        return f"[bold green] Satisfied:[/bold green] [green]{days} days remaining[/green]"
    else:
        return f"[dim] No sales data available[/dim]"

def print_stores_stock():
    console.print(f"\n[bold cyan]Today stock levels: {date.today()}[/bold cyan]")

    for store, products in stores.items():
        avg_spd = round(store_sellsratio[store], 2)
        console.print(f"\n[bold white]{store}[/bold white] [dim]| Avg sells/day: {avg_spd}[/dim]")

        for product, data in products.items():
            quantity = data['quantity']
            spd = data['sells_per_day']
            
            try:
                days = quantity / spd
            except ZeroDivisionError:
                days = None
                
            qty_str = stock_level_color(quantity)
            days_str = days_remaining_color(days)
            console.print(f"  - [white]{product.capitalize()}[/white]: {qty_str} units | [dim]{spd} SpD[/dim] | {days_str}")


def print_inventory():
    console.print(f"\n[bold cyan]Warehouse Inventory: {date.today()}[/bold cyan]")
    for product, data in inventory.items():
        if data['stock'] == 0:
            console.print(f"  - [bold red]{product.capitalize()}: [italic]NO STOCK[/italic][/bold red] | [dim]Days remaining: {data['daysremaining']}[/dim]")
        
        elif data['daysremaining'] == 0:
            console.print(f"  - [bold red]{product.capitalize()}: {data['stock']}[/bold red] | [dim]Days remaining: {data['daysremaining']}[/dim] ")
        elif data['daysremaining'] < 4:
            console.print(f"  - [bold yellow]{product.capitalize()}: {data['stock']}[/bold yellow] | [yellow]Days remaining: {data['daysremaining']}[/yellow]")
        else:
            console.print(f"  - [bold green]{product.capitalize()}: {data['stock']}[/bold green] | [green]Days remaining: {data['daysremaining']}[/green]")


def inventory_control():
    while True:
        print_inventory()
        opt = input('\nCome back [0] | Refill stock [1] | Organize by quantity [2] | Organize by name [3]: ')
        if opt == '0':
            break
        elif opt == '1':
            console.print("\n[bold red]Products with low stock:[/bold red]")
            for product, data in sorted(inventory.items(), key=lambda x: x[1]['stock'], reverse=True):
                if data['daysremaining'] < 2:
                    console.print(f"  - [red]{product.upper()}[/red]: {stock_level_color(data['stock'])} | [dim]Days remaining: {data['daysremaining']}[/dim]")
            selected_product = input('Which one do you want to refill?: ')
            if selected_product in inventory:
                inventory[selected_product]['stock'] += int(input('How many units do you want to add?: '))
                console.print(f"[green]Stock updated for {selected_product}[/green]")
                inventory_daysRemaining()
            else:
                console.print('[red]Product not found.[/red]')
        elif opt == '2':
            sorted_inventory = sorted(inventory.items(), key=lambda x: x[1]['stock'], reverse=True)
            console.print("\n[bold cyan]Inventory by quantity:[/bold cyan]")
            for product, data in sorted_inventory:
                console.print(f"  - {product}: {stock_level_color(data['stock'])}")
        elif opt == '3':
            sorted_inventory = sorted(inventory.items(), key=lambda x: x[0])
            console.print("\n[bold cyan]Inventory by name:[/bold cyan]")
            for product, data in sorted_inventory:
                console.print(f"  - [white]{product.upper()}[/white]: {stock_level_color(data['stock'])}")


def save_inventory():
    with open('warehouse_inventory.txt', 'w') as f:
        for product, data in inventory.items():
            f.write(f"product {product} stock {data['stock']}\n")


def save_changes():
    save_inventory()
    with open('stores_inventory_stock.txt', 'w') as f:
        for store, products in stores.items():
            f.write(f"\nStore: {store}\n")
            for product, data in products.items():
                f.write(f"product: {product} , quantity: {data['quantity']} , sells_per_day: {data['sells_per_day']}\n")


def manual_distribution(selected_product):
    console.print('[dim]------------------------------------------------------------[/dim]')
    i = 0
    for store, products in stores.items():
        for product, data in products.items():
            opt = input(f"Come back [0] | Distribute to a specific store[1] | Distribute to all stores [2]: ")
            if opt == '0':
                return
            elif opt == '1':
               store_selected = input('Which store do you want to distribute to? put the number: ')
               if product == selected_product:
                    i += 1
                    stores_stock = data['quantity']
                    
                    try:
                        distribution = int(input(f"{i}) {store} has: {stores_stock} in stock | {product} warehouse stock: {inventory[product]['stock']} | You distribute: "))
                    except ValueError:
                        if distribution == '':
                            return
                        console.print('[red]Invalid input. Please enter a number.[/red]')
                        continue
            elif opt == '2':
                if product == selected_product:
                    i += 1
                    stores_stock = data['quantity']
                    
                    try:
                        distribution = int(input(f"{i}) {store} has: {stores_stock} in stock | {product} warehouse stock: {inventory[product]['stock']} | You distribute: "))
                    except ValueError:
                        if distribution == '':
                            return
                        console.print('[red]Invalid input. Please enter a number.[/red]')
                        continue
            
                       
            if distribution <= inventory[selected_product]['stock'] and distribution <= stores_stock:
                if store not in items_distributed:
                    items_distributed[store] = {}
                if product not in items_distributed[store]:
                    items_distributed[store][product] = 0
                items_distributed[store][product] += distribution

                inventory[selected_product]['stock'] -= distribution
                stores[store][product]['quantity'] += distribution
                console.print(f"[green]Distributed {distribution} units of {product} to {store}.[/green]")
            
            elif distribution > inventory[selected_product]['stock']:
                console.print(f"[red]Not enough stock available for {product}.[/red]")
            elif distribution > stores_stock:
                console.print(f"[red]Cannot distribute more than the requested amount for {store}.[/red]")
            else:
                console.print(f"[red]Cannot distribute {distribution} units. Check stock and stores_stock.[/red]")
        inventory_daysRemaining()


def print_stores_stock_for_product(selected_product, print_stock=True):
    n = 0
    stores = []
    if selected_product not in inventory:
        console.print('[red]Product not found in inventory.[/red]')
        return
    if print_stock:
        stock = inventory[selected_product]['stock']
        console.print(f"\n[bold white]{selected_product.capitalize()} in warehouse:[/bold white] {stock_level_color(stock)}")
        for store, products in stores.items():
            for product, data in products.items():
                if product == selected_product:
                    stores.append((store, data))
                    if data['quantity'] > 0:
                        n += 1
                        console.print(f"  [bold]{n}- {store}:[bold] [yellow]Has {data['quantity']} {product} in stock[/yellow] | [bold]Days remaining:[/bold] {days_remaining_color(0, data['quantity'], data['sells_per_day'])}")
                    else:
                        n += 1
                        console.print(f"  [bold red]{n}- {store}: {product.capitalize()} out of stock[/bold red]")


def manual_distribution_menu(selected_product):
    s_product = selected_product
    print_stores_stock_for_product(s_product, print_stock=True)
    while True:
        if inventory[s_product]['stock'] == 0:
            console.print(f"[bold red]No stock available for {s_product}.[/bold red]")
            s_product = input('List of products in stock [0] | Distribute another product [write it]: ')
            if s_product == '0':
                break
            print_stores_stock_for_product(s_product, print_stock=True)
        else:
            manual_distribution(s_product)
            print_stores_stock_for_product(s_product, print_stock=True)
            opt = input('List of products in stock [0] | Distribute more [1]: ')
            if opt == '0':
                break


def automated_distribution():
    console.print('[yellow]Automated distribution coming soon...[/yellow]')


def main():
    console.print(f"\n[bold cyan]Distribution System - {date.today()}[/bold cyan]")
    while True:
        console.print("\n[dim]------------------------------------------------------------[/dim]")
        opt = input('Exit [0] | Stores stock [1] | Warehouse inventory [2] | Manual distribution [3] | Automated distribution [4] | Distributed products [5]: ')
        
        # Exit
        if opt == '0':
            console.print('[bold red]Exiting...[/bold red]')
            break
        
        # Stores stock
        elif opt == '1':
            parse_data()
            print_stores_stock()
        
        # Warehouse inventory
        elif opt == '2':
            parse_data()
            inventory_control()

        # Manual distribution
        elif opt == '3':
            print_inventory()
            while True:
                selected_product = input('Main menu [0] | Select product to distribute [write it]: ')
                if selected_product == '0':
                    break
                if selected_product not in inventory:
                    console.print('[red]Product not found.[/red]')
                    continue
                if inventory[selected_product]['stock'] == 0:
                    console.print('[bold red]No stock available for this product.[/bold red]')
                    continue
                manual_distribution_menu(selected_product)
                print_inventory()

        # Automated distribution
        elif opt == '4':
            automated_distribution()

        # Distributed products
        elif opt == '5':
            while True:
                console.print(f"\n[bold cyan]Products distributed on {date.today()}:[/bold cyan]")
                if not items_distributed:
                    console.print("[yellow]No products have been distributed yet.[/yellow]")
                for store, products in items_distributed.items():
                    console.print(f"\n[bold white]{store}:[/bold white]")
                    for product, distribution in products.items():
                        console.print(f"  - [green]{product}: {distribution} units[/green]")
                opt = input('Come back [0] | Save distribution [1]: ')
                if opt == '0':
                    break
                elif opt == '1':
                    save_changes()
                    items_distributed.clear()
                    console.print('[green]Distribution saved successfully.[/green]')
                else:
                    console.print('[red]Invalid option. Please try again.[/red]')


if __name__ == "__main__":
    main()