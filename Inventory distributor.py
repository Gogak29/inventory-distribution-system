import time
from datetime import date
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich import box

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
            days_remaining = sells_per_day and round(quantity / sells_per_day, 1) or 0.0
            stores[store][product] = {
                'quantity': quantity,
                'sells_per_day': sells_per_day,
                'days_remaining': days_remaining,
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

def update_days_remaining():
    for store, products in stores.items():
        for product, data in products.items():
            spd = data['sells_per_day']
            qty = data['quantity']
            stores[store][product]['days_remaining'] = spd and round(qty / spd, 1) or 0.0    
    
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


def days_remaining_color(days):
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
            days = data['days_remaining']

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

            selected_products = input('\nWhich product do you want to readjust? (or 0 to go back): ').strip().lower()
            if selected_products == '0':
                continue
            if selected_products in inventory:
                try:
                    units = int(input('How many units do you want to add/substract? put -# to substract: '))
                    old_stock = inventory[selected_products]['stock']
                    inventory[selected_products]['stock'] += units
                    inventory_daysRemaining()
                    console.print(f"[green]Stock updated for [bold]{selected_products}[/bold] from {old_stock} to {inventory[selected_products]['stock']}.[/green]")
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


def manual_distribution(selected_products, option=None, selected_store=None):
    console.print('[dim]------------------------------------------------------------[/dim]')
    i = 0
    s = 0
    distribution = 0
    n_selected_store = 0
    
    if selected_store.isdigit():
        n_selected_store = int(selected_store)
    
    for store, products in stores.items():
        s += 1
        for product, data in products.items():
            stores_stock = data['quantity']
            if product == selected_products:
                if option == '1':                  
                    if s == n_selected_store or selected_store.lower() == store.lower():
                        try:
                            distribution = int(input(f"{s}) {store} has: {stores_stock} in stock | {product} warehouse stock: {inventory[product]['stock']} | You distribute: "))
                        except ValueError:
                            if distribution == '':
                                return
                            elif distribution > inventory[selected_products]['stock']:
                                console.print(f"[red]Not enough stock available for {product}.[/red]")
                                time.sleep(1)
                                return
                            console.print('[red]Invalid input. Please enter a number.[/red]')
                            time.sleep(1)
                            return
                
                elif option == '2':
                    i += 1
                    if inventory[selected_products]['stock'] == 0:
                        return
                    try:
                        distribution = int(input(f"{i}) {store} has: {stores_stock} in stock | {product} warehouse stock: {inventory[product]['stock']} | You distribute: "))
                    except ValueError:
                        if distribution == '':
                            return
                        console.print('[red]Invalid input. Please enter a number.[/red]')
                        time.sleep(1)
                        continue
                
                if selected_store is not None and(s != n_selected_store and selected_store.lower() != store.lower()):
                    continue        
                
                if distribution <= inventory[selected_products]['stock']:
                    if store not in items_distributed:
                        items_distributed[store] = {}
                    if product not in items_distributed[store]:
                        items_distributed[store][product] = 0
                        
                    items_distributed[store][product] += distribution
                    inventory[selected_products]['stock'] -= distribution
                    stores[store][product]['quantity'] += distribution
                    console.print(f"[green]Distributed {distribution} units of {product} to {store}.[/green][bold] Stock: {stores_stock} → {stores_stock + distribution}.[/bold]")
                
                elif distribution > inventory[selected_products]['stock']:
                    console.print(f"[red]Not enough stock available for {product}.[/red]")
                else:
                    console.print(f"[red]Cannot distribute {distribution} units. Check stock and store stock.[/red]")
            inventory_daysRemaining()
            update_days_remaining()
    time.sleep(1.5)

def manual_distribution_menu(selected_products):
    sel_product = selected_products
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
                sel_store = input('Which store do you want to distribute to? put the number or the store name: ')
                
                if sel_store.isdigit():
                    selected_store = int(sel_store)
                    if selected_store < 1 or selected_store > len(stores):
                        console.print('[red]Invalid store number. Please try again.[/red]')
                        continue
                    
                manual_distribution(sel_product, opt, sel_store)
            
            if opt == '2':
                sel_store = None
                manual_distribution(sel_product, opt, sel_store)
                
            print_stores_stock_for_product(sel_product, print_stock=True)


def print_stores_stock_for_product(selected_products, print_stock=True):
    if print_stock:
        table = Table(box=box.SIMPLE_HEAVY, show_lines=False)
        table.add_column("#", justify="right", style="bold")
        table.add_column("Store", style="bold")
        table.add_column("Product", style="bold")
        table.add_column("Quantity", justify="right")
        table.add_column("Days Remaining", justify="right")

    n = 0
    for product in selected_products:
        if product not in inventory:
            console.print('[red]Product not found in inventory.[/red]')
            return
        stock = inventory[product]['stock']
        console.print(f"[bold white]{product.capitalize()} in warehouse:[/bold white] {stock_level_color(stock)}")
    console.print(f"[dim]------------------------------------------------------------[/dim]")
    
    for store, products in stores.items():
        n += 1
        table.add_row(str(f'[bold blue]{n}[/bold blue]'),
                        store,'-', '-', '-')
        for product in selected_products:
            for product_name, data in products.items():
                if product == product_name:
                    table.add_row(
                        '',
                        '',
                        product_name.capitalize(),
                        str(data['quantity']),
                        days_remaining_color(data['days_remaining']),
                    )

    console.print(table)


TARGET_DAYS = 7          # How many days of stock a store should ideally have
URGENT_DAYS = 4          # Below this = urgent (shown in red)
LOW_DAYS    = 6          # Below this = low stock (shown in yellow)


def automated_distribution(selected_products, selected_stores=None, target_days=TARGET_DAYS):


    store_needs = {}       # { store_name: units_needed }
    store_days  = {}       # { store_name: current days_remaining }
    
    if selected_stores is None:
        selected_stores = list(stores.keys())
    for selected_product in selected_products:
        warehouse_stock = inventory[selected_product]['stock']

        if warehouse_stock == 0:
            console.print(f"[bold red]No warehouse stock available for {selected_product}.[/bold red]")
            return

        for store in selected_stores:
            if selected_product not in stores[store]:
                continue

            data = stores[store][selected_product]
            spd  = data['sells_per_day']
            qty  = data['quantity']

            days_remaining = (qty / spd) if spd > 0 else 0.0
            store_days[store] = round(days_remaining, 1)

            need = max(0.0, (target_days - days_remaining) * spd)
            store_needs[store] = need

    # ─── STEP 2: Check if anyone actually needs anything ──────────────────────

        total_need = sum(store_needs.values())

        if total_need == 0:
            console.print(f"\n[bold green]All stores already have >= {target_days} days of {selected_product}.[/bold green]")
            return

    # ─── STEP 3: Preview table before distributing ───────────────────────────
    #
    # Show the user what will happen before committing — good UX practice.

        console.print(f"\n[bold cyan]Automated distribution for: {selected_product.capitalize()}[/bold cyan]")
        console.print(f"[dim]Target: {target_days} days | Warehouse stock: {warehouse_stock} units | Total need: {round(total_need)} units[/dim]\n")

        _preview_distribution_table(
            selected_product, store_needs, store_days,
            warehouse_stock, target_days
        )

        # ─── STEP 4: Ask for confirmation ─────────────────────────────────────────

        confirm = input("\nProceed with this distribution? [y/n]: ").strip().lower()
        if confirm != 'y':
            console.print("[yellow]Distribution cancelled.[/yellow]")
            return

        # ─── STEP 5: Allocate units proportionally ────────────────────────────────
        
        allocations = _proportional_allocate(store_needs, warehouse_stock)

        total_distributed = 0

        for store, units in allocations.items():
            if units <= 0:
                continue

            # Safety check — never distribute more than what's left in the warehouse
            units = min(units, inventory[selected_product]['stock'])
            if units <= 0:
                continue

            # Update warehouse stock
            inventory[selected_product]['stock'] -= units

            # Update store stock
            stores[store][selected_product]['quantity'] += units

            # Log in items_distributed (used by the "show distributed" menu)
            if store not in items_distributed:
                items_distributed[store] = {}
            items_distributed[store][selected_product] = (
                items_distributed[store].get(selected_product, 0) + units
            )

            total_distributed += units
            console.print(
                f"  [green]→ {store}:[/green] +{units} units "
                f"[dim](was {round(store_days[store], 1)} days → "
                f"now ~{round(store_days[store] + units / stores[store][selected_product]['sells_per_day'], 1)} days)[/dim]"
            )

        # ─── STEP 7: Refresh computed fields ──────────────────────────────────────

        update_days_remaining()
        inventory_daysRemaining()

        remaining = inventory[selected_product]['stock']
        console.print(
            f"\n[bold green]Done. [/bold green] Distributed {total_distributed} units. "
            f"Warehouse remaining: {remaining} units."
        )


def _proportional_allocate(store_needs: dict, available: float) -> dict:

    total_need = sum(store_needs.values())

    if total_need == 0:
        return {store: 0 for store in store_needs}

    if available >= total_need:
        return {store: int(need) for store, need in store_needs.items()}

    pool = float(available)
    allocations = {}
    rank = {}
    leftover = 0.0

    for store, need in store_needs.items():
        share = need / total_need
        ideal = share * pool

        allocations[store] = int(ideal)          # floor — whole units only
        remainder = ideal - int(ideal)           # fractional part lost to rounding
        rank[store] = remainder
        leftover += remainder                     # accumulate all lost fractions

    # sort by biggest remainder — most shortchanged stores first
    rank = dict(sorted(rank.items(), key=lambda x: x[1], reverse=True))

    leftover = int(leftover)  # only whole units can be distributed
    for store in rank:
        if leftover <= 0:
            break
        allocations[store] += 1
        leftover -= 1

    return allocations


def _preview_distribution_table(
    product, store_needs, store_days, warehouse_stock, target_days
):
    total_need = sum(store_needs.values())
    allocations = _proportional_allocate(store_needs, warehouse_stock)

    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Store",          style="white",  min_width=20)
    table.add_column("Current days",   justify="right")
    table.add_column("Need (units)",   justify="right")
    table.add_column("Share %",        justify="right")
    table.add_column("Will receive",   justify="right")
    table.add_column("Days after",     justify="right")

    sorted_stores = sorted(store_needs.keys(), key=lambda s: store_days[s])

    for store in sorted_stores:
        need  = store_needs[store]
        days  = store_days[store]
        units = int(allocations.get(store, 0))
        spd   = stores[store][product]['sells_per_day']

        share_pct = f"{round(need / total_need * 100)}%" if total_need > 0 else "0%"
        days_after = round(days + units / spd, 1) if spd > 0 else days

        # Color-code current days
        if days < URGENT_DAYS:
            days_str = f"[bold red]{days}[/bold red]"
        elif days < LOW_DAYS:
            days_str = f"[yellow]{days}[/yellow]"
        else:
            days_str = f"[green]{days}[/green]"

        # Color-code units received
        units_str = f"[green]+{units}[/green]" if units > 0 else "[dim]0[/dim]"

        table.add_row(store, days_str, str(round(need)), share_pct, units_str, str(days_after))

    console.print(table)
    console.print(f"\n[dim]Warehouse stock: {warehouse_stock} | Total needed: {round(total_need)} | "
                  f"{'[green]Enough for all[/green]' if warehouse_stock >= total_need else '[yellow]Partial distribution[/yellow]'}[/dim]")


def automated_distribution_menu(selected_products):
    product_label = ", ".join(selected_products)
    console.print(f"\n[bold cyan]Automated distribution — {product_label}[/bold cyan]")
    print_stores_stock_for_product(selected_products, print_stock=True)

    while True:
        console.print("\n[dim]------------------------------------------------------------[/dim]")
        opt = input(
            f"Back [0] | Distribute to all stores [1] | "
            f"\nDistribute to specific stores [2] | Change target days [3]: "
        ).strip()

        if opt == '0':
            return

        elif opt == '1':
            automated_distribution(selected_products)

        elif opt == '2':
            print_stores_stock_for_product(selected_products, print_stock=False)
            raw = input("Enter store numbers or names, comma-separated: ")
            selected = _parse_store_selection(raw)

            if not selected:
                console.print("[red]No valid stores selected.[/red]")
                continue

            automated_distribution(selected_products, selected_stores=selected)

        elif opt == '3':
            try:
                new_target = float(input(f"New target days (current: {TARGET_DAYS}): "))
                if new_target <= 0:
                    raise ValueError
                automated_distribution(selected_products, target_days=new_target)
            except ValueError:
                console.print("[red]Invalid number.[/red]")

        else:
            console.print("[red]Invalid option.[/red]")

        print_stores_stock_for_product(selected_products, print_stock=True)


def _parse_store_selection(raw_input: str) -> list:
    store_list = list(stores.keys())
    selected   = []
    for token in raw_input.split(','):
        token = token.strip()

        if not token:
            continue

        if token.isdigit():
            idx = int(token) - 1          # user sees 1-based numbers
            if 0 <= idx < len(store_list):
                selected.append(store_list[idx])
            else:
                console.print(f"[yellow]Store #{token} not found, skipping.[/yellow]")
        else:
            # Try case-insensitive name match
            match = next((s for s in store_list if s.lower() == token.lower()), None)
            if match:
                selected.append(match)
            else:
                console.print(f"[yellow]Store '{token}' not found, skipping.[/yellow]")

    return selected
        
        

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
            print_stores_stock()
        
        # Warehouse inventory
        elif opt == '2':
            inventory_control()

        # Manual distribution or automated distribution
        elif opt == '3':
            print_inventory()
            while True:
                selected_products = input('Main menu [0] | Select product to distribute [write it]: ')
                if selected_products == '0':
                    break
                if selected_products not in inventory:
                    console.print('[red]Product not found.[/red]')
                    continue
                if inventory[selected_products]['stock'] == 0:
                    console.print('[bold red]No stock available for this product.[/bold red]')
                    continue
                manual_distribution_menu(selected_products)
                print_inventory()
        
        elif opt == '4':
            print_inventory()
            while True:
                selected_products = input('Main menu [0] | Write the products to distribute divided by commas: ')
                if selected_products == '0':
                    break
                selected_products = [product.strip().lower() for product in selected_products.split(',')]
                for product in selected_products:
                    if product not in inventory:
                        console.print(f'[red]Product "{product}" not found.[/red]')
                        time.sleep(1)
                        continue
                    if inventory[product]['stock'] == 0:
                        console.print(f'[bold red]No stock available for product "{product}".[/bold red]')
                        time.sleep(1)
                        continue
                automated_distribution_menu(selected_products)
                print_inventory()
                
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
                    parse_data()
                else:
                    console.print('[red]Invalid option. Please try again.[/red]')


if __name__ == "__main__":
    main()