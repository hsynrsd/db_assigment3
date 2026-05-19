# Import all libraries we will use in this notebook.

# main.py

import sqlite3
import random
from datetime import datetime, timedelta
from random import randint, randrange

from faker import Faker
import pandas as pd

# Create a Faker instance localised to Austrian German for realistic names.
fake = Faker('de_AT')

# Fix the random seed so the "random" data is reproducible;
# when the grader runs your notebook, the same values appear.
random.seed(42)
Faker.seed(42)

print("Setup complete. Libraries are ready.")

# Open (or create) the database file and connect to it.
conn = sqlite3.connect('kremsfix.db')

# Create a cursor; we use it to execute SQL statements.
cursor = conn.cursor()

# SQLite does not enforce foreign keys by default; turn it on.
cursor.execute("PRAGMA foreign_keys = ON;")

print("Connected to kremsfix.db.")

# Add every table you create to this list, in reverse dependency order.
tables_to_drop = [
    'ContactEvent', 'Payment', 'UsedPart', 'RepairEmployee',
    'Part', 'Repair', 'Ticket', 'Supplier', 'Employee', 'Customer'
]

for table_name in tables_to_drop:
    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")

conn.commit()

print(f"Checked {len(tables_to_drop)} tables for drop.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customer (
        customer_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name                 TEXT    NOT NULL,
        phone_number         TEXT    NOT NULL UNIQUE,
        email                TEXT,
        customer_type        TEXT    NOT NULL CHECK(customer_type IN ('private', 'corporate')),
        discount_eligibility TEXT    NOT NULL DEFAULT 'None',
        company_name         TEXT,
        tax_number           TEXT
    );
""")

conn.commit()

print("Customer table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Employee (
        employee_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name      TEXT    NOT NULL,
        last_name       TEXT    NOT NULL,
        phone           TEXT    NOT NULL UNIQUE,
        email           TEXT    NOT NULL UNIQUE,
        occupation      TEXT    NOT NULL
    );
""")

conn.commit()

print("Employee table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Supplier (
        name            TEXT PRIMARY KEY NOT NULL,
        location        TEXT NOT NULL
    );
""")

conn.commit()

print("supplier table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ticket (
        ticket_no       INTEGER PRIMARY KEY AUTOINCREMENT,
        intake_date     TEXT    NOT NULL,
        problem         TEXT    NOT NULL,
        speed_estimate  TEXT    NOT NULL,
        device_name     TEXT    NOT NULL,
        passcode        TEXT,
        status          TEXT    NOT NULL CHECK(status IN ('Waiting', 'In progress', 'Waiting for parts', 'Done', 'Picked up', 'Unclaimed')),
        rush_order      INTEGER NOT NULL CHECK(rush_order IN (0, 1)),
        total_price     REAL    NOT NULL DEFAULT 0.0,
        is_warranty     INTEGER NOT NULL CHECK(is_warranty IN (0, 1)),
        deposit         REAL    NOT NULL DEFAULT 0.0,
        customer_id     INTEGER NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
    );
""")

conn.commit()

print("ticket table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Repair (
        repair_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        repair_type     TEXT    NOT NULL,
        price           REAL    NOT NULL DEFAULT 0.0,
        ticket_no       INTEGER NOT NULL,
        employee_id     INTEGER NOT NULL,
        FOREIGN KEY (ticket_no) REFERENCES Ticket(ticket_no),
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
    );
""")

conn.commit()

print("repair table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Part (
        part_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        serial_number   INTEGER,
        quality         TEXT    NOT NULL CHECK(quality IN ('good', 'mid', 'bad')),
        manufacturer    TEXT    NOT NULL,
        part_type       TEXT    NOT NULL,
        purchase_price  REAL    NOT NULL DEFAULT 0.0,
        name            TEXT    NOT NULL,
        FOREIGN KEY (name) REFERENCES Supplier(name)
    );
""")

conn.commit()

print("part table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS UsedPart (
        repair_id       INTEGER,
        part_id         INTEGER,
        quantity        INTEGER NOT NULL DEFAULT 1,
        is_defective    INTEGER NOT NULL CHECK(is_defective IN (0, 1)),
        PRIMARY KEY(repair_id, part_id),
        FOREIGN KEY (repair_id) REFERENCES Repair(repair_id),
        FOREIGN KEY (part_id) REFERENCES Part(part_id)
    );
""")

conn.commit()

print("usedpart table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payment (
        payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_amount  REAL    NOT NULL,
        payment_method  TEXT    NOT NULL CHECK(payment_method IN ('check', 'card', 'cash')),
        ticket_no       INTEGER NOT NULL,
        FOREIGN KEY (ticket_no) REFERENCES Ticket(ticket_no)
    );
""")

conn.commit()

print("Payment table created.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ContactEvent (
        event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        message         TEXT    NOT NULL,
        contact_type    TEXT    NOT NULL CHECK(contact_type IN ('call', 'sms', 'email')),
        contact_address TEXT    NOT NULL,
        ticket_no       INTEGER NOT NULL,
        FOREIGN KEY (ticket_no) REFERENCES Ticket(ticket_no)
    );
""")

conn.commit()

print("ContactEvent table created.")

print("All tables created successfully.")

# random data start

# 1. Customers
num_customers = 50

for i in range(num_customers):

    # 80% private customers, 20% corporate.
    c_type = random.choices(['private', 'corporate'], weights=[0.8, 0.2])[0]

    full_name = fake.name()

    # Split the full name into first and last name;
    # cause in our ER diagram we have only "name" for customers.

    phone_number = fake.unique.phone_number()

    # Around 70% of customers give an email address;
    # the rest do not.
    email = fake.email() if random.random() < 0.7 else None

    # Companies have a company name and an Austrian tax number;
    # private customers do not.
    company = fake.company() if c_type == 'corporate' else None

    tax_nr = f"ATU{random.randint(10000000, 99999999)}" if c_type == 'corporate' else None

    discount_eligibility = (
        random.choice(['None', 'Silver', 'Gold'])
        if c_type == 'corporate'
        else 'None'
    )

    cursor.execute("""
        INSERT INTO Customer
            (name, phone_number, email, customer_type,
             discount_eligibility, company_name, tax_number)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        full_name,
        phone_number,
        email,
        c_type,
        discount_eligibility,
        company,
        tax_nr
    ))

conn.commit()

print(f"Inserted {num_customers} customers.")

# 2. Suppliers (~5)
num_suppliers = 5
supplier_names = []

for i in range(num_suppliers):
    s_name = fake.unique.company()
    location = fake.city()

    supplier_names.append(s_name)

    cursor.execute("""
        INSERT INTO Supplier (name, location)
        VALUES (?, ?);
    """, (s_name, location))

# 3. Employees
num_employees = 5

occupations = ['repair tech', 'front desk', 'accountant']

for i in range(num_employees):

    emp_f = fake.first_name()
    emp_l = fake.last_name()

    phone = fake.unique.phone_number()
    email = fake.unique.email()

    # Force the first employee to be a repair tech,
    # randomise the rest.
    occupation = 'repair tech' if i == 0 else random.choice(occupations)

    cursor.execute("""
        INSERT INTO Employee
            (first_name, last_name, phone, email, occupation)
        VALUES (?, ?, ?, ?, ?);
    """, (
        emp_f,
        emp_l,
        phone,
        email,
        occupation
    ))

# 4. Parts Catalog
num_parts = 30

part_categories = [
    'screen',
    'battery',
    'camera',
    'motherboard',
    'housing',
    'port',
    'fingerprint reader'
]

for i in range(num_parts):

    serial_number = random.randint(10000000, 99999999)

    chosen_supplier = random.choice(supplier_names)

    quality = random.choice(['good', 'bad', 'mid'])

    manufacturer = fake.company()

    part_type = random.choice(part_categories)

    cost = round(random.uniform(15.0, 90.0), 2)

    cursor.execute("""
        INSERT INTO Part
            (serial_number, quality, manufacturer,
             part_type, purchase_price, name)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (
        serial_number,
        quality,
        manufacturer,
        part_type,
        cost,
        chosen_supplier
    ))

conn.commit()

# Fetch foreign key foundations

cursor.execute("SELECT customer_id FROM Customer;")
customer_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("""
    SELECT employee_id
    FROM Employee
    WHERE occupation = 'repair tech';
""")

tech_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT part_id FROM Part;")
part_pool = [row[0] for row in cursor.fetchall()]

phone_models = [
    ('Apple', 'iPhone 12'),
    ('Apple', 'iPhone 13'),
    ('Apple', 'iPhone 14'),
    ('Samsung', 'Galaxy S21'),
    ('Samsung', 'Galaxy S22'),
    ('Samsung', 'Galaxy A53'),
    ('Google', 'Pixel 7'),
    ('Xiaomi', 'Redmi Note 11')
]

repair_types = [
    ('Screen replacement', 120, 250),
    ('Battery replacement', 60, 120),
    ('Charging port repair', 70, 140),
    ('Back glass replacement', 80, 180),
    ('Water damage diagnosis', 25, 25),
    ('Data recovery', 40, 150)
]

statuses = [
    'Waiting',
    'In progress',
    'Waiting for parts',
    'Done',
    'Picked up',
    'Unclaimed'
]

# 5. Tickets (~200), Repairs (~250),
# UsedParts (~400), and Payments

num_tickets = 200

# Counters to track our exact volumes
total_repairs_generated = 0
total_parts_generated = 0

for i in range(num_tickets):

    chosen_id = random.choice(customer_ids)

    problem = fake.text(max_nb_chars=80)

    speed_estimate = random.choice([
        '1 Hour Rush',
        '1-2 Days Standard'
    ])

    brand, model = random.choice(phone_models)

    device_name = f"{brand} {model}"

    password = (
        fake.password(length=random.randint(4, 8))
        if random.random() < 0.7
        else None
    )

    intake_date = fake.date_between(
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 12, 31)
    ).strftime('%Y-%m-%d')

    status = random.choice(statuses)

    rush_order = 1 if 'Rush' in speed_estimate else 0

    is_warranty = random.choices(
        [0, 1],
        weights=[0.9, 0.1]
    )[0]

    deposit = random.choice([0.0, 20.0, 50.0])

    cursor.execute("""
        INSERT INTO Ticket
            (intake_date, problem, speed_estimate,
             device_name, passcode, status,
             rush_order, total_price,
             is_warranty, deposit, customer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, ?);
    """, (
        intake_date,
        problem,
        speed_estimate,
        device_name,
        password,
        status,
        rush_order,
        is_warranty,
        deposit,
        chosen_id
    ))

    t_no = cursor.lastrowid

    ticket_total_price = 0.0

    # 25% of tickets get a second repair
    # to push the 200 tickets to ~250 total repairs.
    num_repairs_for_ticket = random.choices(
        [1, 2],
        weights=[0.75, 0.25]
    )[0]

    for _ in range(num_repairs_for_ticket):

        rep_task, min_p, max_p = random.choice(repair_types)

        repair_price = round(
            random.uniform(min_p, max_p),
            2
        )

        if rush_order == 1:
            repair_price += 20.0

        if is_warranty == 1:
            repair_price = 0.0

        chosen_tech = random.choice(tech_ids)

        cursor.execute("""
            INSERT INTO Repair
                (repair_type, price, ticket_no, employee_id)
            VALUES (?, ?, ?, ?);
        """, (
            rep_task,
            repair_price,
            t_no,
            chosen_tech
        ))

        r_id = cursor.lastrowid

        total_repairs_generated += 1

        ticket_total_price += repair_price

        # Most repairs need 1-3 parts
        # to push our 250 repairs to ~400 total parts.
        num_parts_for_repair = random.choices(
            [1, 2, 3],
            weights=[0.5, 0.4, 0.1]
        )[0]

        # Use random.sample to guarantee
        # we don't pick the same part_id twice
        # for one repair (Composite PK safety).
        sampled_part_ids = random.sample(
            part_pool,
            num_parts_for_repair
        )

        for chosen_part_id in sampled_part_ids:

            is_defective = random.choices(
                [0, 1],
                weights=[0.94, 0.06]
            )[0]

            cursor.execute("""
                INSERT INTO UsedPart
                    (repair_id, part_id, quantity, is_defective)
                VALUES (?, ?, 1, ?);
            """, (
                r_id,
                chosen_part_id,
                is_defective
            ))

            total_parts_generated += 1

    # Update Ticket Total Price
    # with the accumulated repair costs.
    cursor.execute("""
        UPDATE Ticket
        SET total_price = ?
        WHERE ticket_no = ?;
    """, (
        ticket_total_price,
        t_no
    ))

    # Generate Payments for completed jobs.
    if status in ['Done', 'Picked up'] and ticket_total_price > 0:

        cursor.execute("""
            INSERT INTO Payment
                (payment_amount, payment_method, ticket_no)
            VALUES (?, ?, ?);
        """, (
            ticket_total_price,
            random.choice(['check', 'card', 'cash']),
            t_no
        ))

    # Generate random Contact Events.
    if random.random() < 0.4:

        c_type = random.choice(['call', 'sms', 'email'])

        contact_address = (
            fake.phone_number()
            if c_type != 'email'
            else fake.email()
        )

        cursor.execute("""
            INSERT INTO ContactEvent
                (message, contact_type,
                 contact_address, ticket_no)
            VALUES
                ('Status update regarding your device.',
                 ?, ?, ?);
        """, (
            c_type,
            contact_address,
            t_no
        ))

conn.commit()

print(
    f"Generated {num_tickets} Tickets, "
    f"{total_repairs_generated} Repairs, "
    f"and {total_parts_generated} Used Parts."
)