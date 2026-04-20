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




# Parsing of inventory and requests
def parse_data():
    with open('stores_inventory_stock.txt', 'r') as f:
        store_stock = f.readlines()
    with open('warehouse_inventory.txt', 'r') as f:
        warehouse_inventory = f.readlines()
    
    stores.clear()
    store_sellsratio.clear()
    inventory.clear()

    current_store = None
    for line in store_stock:
        if line.startswith('Store:'):
            current_store = line.split(':')[1].strip()
            stores[current_store] = {}
        elif line.startswith('product:') and current_store:
            parts = line.split(',')
            product = parts[0].split(':')[1].strip()
            quantity = int(parts[1].split(':')[1].strip())
            sells_per_day = float(parts[2].split(':')[1].strip())
            stores[current_store][product] = {
                'quantity': quantity,
                'sells_per_day': sells_per_day
            }

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
        inventory[product] = stock


parse_data()


def stock_level_color(quantity):
    if quantity < 70:
        return f"[bold red]{quantity}[/bold red]"
    elif quantity < 130:
        return f"[yellow]{quantity}[/yellow]"
    else:
        return f"[green]{quantity}[/green]"


def days_remaining_color(days):
    days = round(days, 1)
    if days < 4:
        return f"[bold red]{days} days[/bold red]"
    elif days < 6:
        return f"[yellow]{days} days[/yellow]"
    else:
        return f"[green]{days} days[/green]"


def print_stores_stock():
    console.print(f"\n[bold cyan]Today stock levels: {date.today()}[/bold cyan]")

    for store, products in stores.items():
        avg_spd = round(store_sellsratio[store], 2)
        console.print(f"\n[bold white]{store}[/bold white] [dim]| Avg sells/day: {avg_spd}[/dim]")

        for product, data in products.items():
            quantity = data['quantity']
            spd = data['sells_per_day']
            days = quantity / spd if spd > 0 else 999
            qty_str = stock_level_color(quantity)
            days_str = days_remaining_color(days)
            console.print(f"  - [white]{product.capitalize()}[/white]: {qty_str} units | [dim]{spd} SpD[/dim] | {days_str} remaining")


def print_inventory():
    console.print(f"\n[bold cyan]Warehouse Inventory: {date.today()}[/bold cyan]")
    for product, stock in inventory.items():
        if stock == 0:
            console.print(f"  - [bold red]{product.capitalize()}: NO STOCK[/bold red]")
        elif stock < 100:
            console.print(f"  - [yellow]{product.capitalize()}: {stock}[/yellow]")
        else:
            console.print(f"  - [green]{product.capitalize()}: {stock}[/green]")


def inventory_control():
    while True:
        print_inventory()
        opt = input('\nCome back [0] | Refill stock [1] | Organize by quantity [2] | Organize by name [3]: ')
        if opt == '0':
            break
        elif opt == '1':
            console.print("\n[bold red]Products with NO STOCK:[/bold red]")
            for product, stock in inventory.items():
                if stock == 0:
                    console.print(f"  - [red]{product.upper()}[/red]")
            selected_product = input('Which one do you want to refill?: ')
            if selected_product in inventory:
                inventory[selected_product] += int(input('How many units do you want to add?: '))
                console.print(f"[green]Stock updated for {selected_product}[/green]")
            else:
                console.print('[red]Product not found.[/red]')
        elif opt == '2':
            sorted_inventory = sorted(inventory.items(), key=lambda x: x[1], reverse=True)
            console.print("\n[bold cyan]Inventory by quantity:[/bold cyan]")
            for product, stock in sorted_inventory:
                console.print(f"  - {product}: {stock_level_color(stock)}")
        elif opt == '3':
            sorted_inventory = sorted(inventory.items(), key=lambda x: x[0])
            console.print("\n[bold cyan]Inventory by name:[/bold cyan]")
            for product, stock in sorted_inventory:
                console.print(f"  - [white]{product.upper()}[/white]: {stock_level_color(stock)}")


def save_inventory():
    with open('warehouse_inventory.txt', 'w') as f:
        for product, stock in inventory.items():
            f.write(f"product {product} stock {stock}\n")


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
            if product == selected_product:
                i += 1
                request = data['quantity']
                
                try:
                    distribution = int(input(f"{i}) {store} needs: {request} | {product} stock: {inventory[product]} | You distribute: "))
                except ValueError:
                    console.print('[red]Invalid input. Please enter a number.[/red]')
                    continue
                
                if distribution <= inventory[selected_product] and distribution <= request:
                    if store not in items_distributed:
                        items_distributed[store] = {}
                    if product not in items_distributed[store]:
                        items_distributed[store][product] = 0
                    items_distributed[store][product] += distribution

                    inventory[selected_product] -= distribution
                    stores[store][product]['quantity'] -= distribution
                    console.print(f"[green]Distributed {distribution} units of {product} to {store}.[/green]")
                
                elif distribution > inventory[selected_product]:
                    console.print(f"[red]Not enough stock available for {product}.[/red]")
                elif distribution > request:
                    console.print(f"[red]Cannot distribute more than the requested amount for {store}.[/red]")
                else:
                    console.print(f"[red]Cannot distribute {distribution} units. Check stock and request.[/red]")


def print_stores_stock_for_product(selected_product, print_stock=True):
    ask = False
    n = 0
    if selected_product not in inventory:
        console.print('[red]Product not found in inventory.[/red]')
        return ask
    if print_stock:
        stock = inventory[selected_product]
        console.print(f"\n[bold white]{selected_product.capitalize()} in warehouse:[/bold white] {stock_level_color(stock)}")
        for store, products in stores.items():
            for product, data in products.items():
                if product == selected_product:
                    request = data['quantity']
                    if request > 0:
                        ask = True
                        n += 1
                        console.print(f"  [yellow]{n}- {store}: Needs {request} {product}[/yellow]")
                    else:
                        n += 1
                        console.print(f"  [green]{n}- {store}: {product.capitalize()} satisfied[/green]")
    for store, products in stores.items():
        for product, data in products.items():
            if product == selected_product:
                if data['quantity'] > 0:
                    ask = True
    return ask


def manual_distribution_menu(selected_product):
    s_product = selected_product
    ask = print_stores_stock_for_product(s_product, print_stock=True)
    while True:
        ask = print_stores_stock_for_product(s_product, print_stock=False)
        if inventory[s_product] == 0:
            console.print(f"[bold red]No stock available for {s_product}.[/bold red]")
            s_product = input('List of products in stock [0] | Distribute another product [write it]: ')
            if s_product == '0':
                break
            print_stores_stock_for_product(s_product, print_stock=True)
        else:
            if not ask:
                console.print(f"[green]All requests for {s_product} have been satisfied.[/green]")
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

        if opt == '0':
            console.print('[bold red]Exiting...[/bold red]')
            break

        elif opt == '1':
            parse_data()
            print_stores_stock()

        elif opt == '2':
            parse_data()
            inventory_control()

        elif opt == '3':
            print_inventory()
            while True:
                selected_product = input('Main menu [0] | Select product to distribute [write it]: ')
                if selected_product == '0':
                    break
                if selected_product not in inventory:
                    console.print('[red]Product not found.[/red]')
                    continue
                if inventory[selected_product] == 0:
                    console.print('[bold red]No stock available for this product.[/bold red]')
                    continue
                manual_distribution_menu(selected_product)
                print_inventory()

        elif opt == '4':
            automated_distribution()

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