import time
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
            inventory[product]['daysremaining'] = 0
                
                    
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


def print_inventory(items=None):
    console.print(f"\n[bold cyan]Warehouse Inventory: {date.today()}[/bold cyan]")
    # If no custom list is passed, use the full inventory
    entries = items if items is not None else inventory.items()
    for product, data in entries:
        dr = data['daysremaining']
        stock = data['stock']
        name = product.capitalize()

        if stock == 0:
            console.print(f"  - [bold red]{name}: [italic]NO STOCK[/italic][/bold red] | [dim]Days remaining: {dr}[/dim]")
        elif dr == 0:
            console.print(f"  - [bold red]{name}: {stock}[/bold red] | [dim]Days remaining: {dr}[/dim]")
        elif dr < 4:
            console.print(f"  - [bold yellow]{name}: {stock}[/bold yellow] | [yellow]Days remaining: {dr}[/yellow]")
        else:
            console.print(f"  - [bold green]{name}: {stock}[/bold green] | [green]Days remaining: {dr}[/green]")


def inventory_control():
    print_inventory()
    sorted_items = inventory.items()  # Default order
    
    while True:
        opt = input(
            f'Come back [0] | Readjust stock [1] | Sort by quantity [2]\n| Sort by name [3] | Sort by days remaining [4]: '
        )

        if opt == '0':
            break

        elif opt == '1':
            urgent = [
                (p, d) for p, d in inventory.items()
                if d['daysremaining'] < 4
            ]
            # Sort ascending so the most urgent (lowest days) appears first
            urgent.sort(key=lambda x: x[1]['daysremaining'])

            if not urgent:
                console.print("\n[green]All products have sufficient stock.[/green]")
            else:
                console.print("\n[bold red]Products with low stock:[/bold red]")
                for product, data in urgent:
                    console.print(
                        f"  - [red]{product.upper()}[/red]: "
                        f"{stock_level_color(data['stock'])} | "
                        f"[dim]Days remaining: {data['daysremaining']}[/dim]"
                    )

            selected_product = input('\nWhich product do you want to readjust? (or 0 to go back): ').strip().lower()
            if selected_product == '0':
                continue
            if selected_product in inventory:
                try:
                    units = int(input('How many units do you want to add/substract? put -# to substract: '))
                    old_stock = inventory[selected_product]['stock']
                    inventory[selected_product]['stock'] += units
                    inventory_daysRemaining()
                    console.print(f"[green]Stock updated for [bold]{selected_product}[/bold] from {old_stock} to {inventory[selected_product]['stock']}.[/green]")
                except ValueError:
                    console.print('[red]Invalid quantity. Please enter a number.[/red]')
            else:
                console.print('[red]Product not found.[/red]')
            time.sleep(2)

        elif opt == '2':
            sorted_items = sorted(inventory.items(), key=lambda x: x[1]['stock'], reverse=True)
            console.print("\n[bold cyan]Sorted by quantity (highest first):[/bold cyan]")

        elif opt == '3':
            sorted_items = sorted(inventory.items(), key=lambda x: x[0])
            console.print("\n[bold cyan]Sorted by name (A → Z):[/bold cyan]")

        elif opt == '4':
            sorted_items = sorted(inventory.items(), key=lambda x: x[1]['daysremaining'], reverse=True)
            console.print("\n[bold cyan]Sorted by days remaining (most urgent first):[/bold cyan]")

        else:
            console.print('[red]Invalid option. Please try again.[/red]')
            time.sleep(1)
        
        print_inventory(sorted_items)

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


def manual_distribution(selected_product, option=None, selected_store=None):
    console.print('[dim]------------------------------------------------------------[/dim]')
    i = 0
    s = 0
    distribution = 0
    
    for store, products in stores.items():
        s += 1
        for product, data in products.items():
            stores_stock = data['quantity']
            if product == selected_product:
                if option == '1':                  
                    if s == selected_store:
                        try:
                            distribution = int(input(f"{selected_store}) {store} has: {stores_stock} in stock | {product} warehouse stock: {inventory[product]['stock']} | You distribute: "))
                        except ValueError:
                            if distribution == '':
                                return
                            console.print('[red]Invalid input. Please enter a number.[/red]')
                            continue
                
                elif option == '2':
                    i += 1
                    
                    try:
                        distribution = int(input(f"{i}) {store} has: {stores_stock} in stock | {product} warehouse stock: {inventory[product]['stock']} | You distribute: "))
                    except ValueError:
                        if distribution == '':
                            return
                        console.print('[red]Invalid input. Please enter a number.[/red]')
                        continue
                
                if selected_store is not None and s != selected_store:
                    continue        
                
                if distribution <= inventory[selected_product]['stock']:
                    if store not in items_distributed:
                        items_distributed[store] = {}
                    if product not in items_distributed[store]:
                        items_distributed[store][product] = 0
                        
                    items_distributed[store][product] += distribution
                    inventory[selected_product]['stock'] -= distribution
                    stores[store][product]['quantity'] += distribution
                    console.print(f"[green]Distributed {distribution} units of {product} to {store}.[/green][bold] Stock: {stores_stock} → {stores_stock + distribution}.[/bold]")
                
                elif distribution > inventory[selected_product]['stock']:
                    console.print(f"[red]Not enough stock available for {product}.[/red]")
                else:
                    console.print(f"[red]Cannot distribute {distribution} units. Check stock and store stock.[/red]")
            inventory_daysRemaining()
    time.sleep(2)


def manual_distribution_menu(selected_product):
    sel_product = selected_product
    print_stores_stock_for_product(sel_product, print_stock=True)
    while True:
        if inventory[sel_product]['stock'] == 0:
            console.print(f"[bold red]No stock available for {sel_product}.[/bold red]")
            sel_product = input('List of products in stock [0] | Distribute another product [write it]: ')
            if sel_product == '0':
                break
            print_stores_stock_for_product(sel_product, print_stock=True)
        else:
            opt = input(f"Come back [0] | Distribute to a specific store [1] | Distribute to all stores [2]: ")
            
            if opt == '0':
                break
            
            if opt == '1':
                try:
                    sel_store = int(input('Which store do you want to distribute to? put the number: '))
                    manual_distribution(sel_product, opt, sel_store)   
                
                except ValueError:
                    console.print('[red]Invalid input. Please enter a number.[/red]')
                if sel_store < 1 or sel_store > len(stores):
                    console.print('[red]Invalid store number. Please try again.[/red]')
                    continue
            
            if opt == '2':
                sel_store = None
                manual_distribution(sel_product, opt, sel_store)
                
            print_stores_stock_for_product(sel_product, print_stock=True)

def print_stores_stock_for_product(selected_product, print_stock=True):
    n = 0
    
    if selected_product not in inventory:
        console.print('[red]Product not found in inventory.[/red]')
        return
    
    if print_stock:
        
        stock = inventory[selected_product]['stock']
        
        console.print(f"\n[bold white]{selected_product.capitalize()} in warehouse:[/bold white] {stock_level_color(stock)}")
        for store, products in stores.items():
            for product, data in products.items():
                if product == selected_product:
                    if data['quantity'] > 0:
                        n += 1
                        console.print(f"  [bold]{n}- {store}:[bold] [yellow]Has {data['quantity']} {product} in stock[/yellow] | [bold]Days remaining:[/bold] {days_remaining_color(0, data['quantity'], data['sells_per_day'])}")
                    else:
                        n += 1
                        console.print(f"  [bold red]{n}- {store}: {product.capitalize()} out of stock[/bold red]")





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