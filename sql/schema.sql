DROP TABLE IF EXISTS lineitem;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS supplier;
DROP TABLE IF EXISTS nation;

CREATE TABLE nation (
    nationid INTEGER PRIMARY KEY,
    name VARCHAR(25) NOT NULL,
    regionid INTEGER NOT NULL,
    comment VARCHAR(152)
);

CREATE TABLE customer (
    cust_id INTEGER PRIMARY KEY,
    name VARCHAR(25) NOT NULL,
    address VARCHAR(40),
    nationid INTEGER NOT NULL,
    phone VARCHAR(15),
    acct_balance DECIMAL(15,2),
    market_segment VARCHAR(10),
    comment VARCHAR(117),
    FOREIGN KEY (nationid) REFERENCES nation(nationid)
);

CREATE TABLE supplier (
    supplierid INTEGER PRIMARY KEY,
    name VARCHAR(25) NOT NULL,
    address VARCHAR(40),
    nationid INTEGER NOT NULL,
    phone VARCHAR(15),
    acct_balance DECIMAL(15,2),
    comment VARCHAR(101),
    FOREIGN KEY (nationid) REFERENCES nation(nationid)
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    cust_id INTEGER NOT NULL,
    order_status CHAR(1),
    total_price DECIMAL(15,2),
    order_date DATE,
    order_priority VARCHAR(15),
    clerk VARCHAR(15),
    ship_priority INTEGER,
    comment VARCHAR(79),
    FOREIGN KEY (cust_id) REFERENCES customer(cust_id)
);

CREATE TABLE lineitem (
    order_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    supplierid INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    quantity DECIMAL(15,2),
    extended_price DECIMAL(15,2),
    discount DECIMAL(15,2),
    tax DECIMAL(15,2),
    return_flag CHAR(1),
    line_status CHAR(1),
    ship_date DATE,
    commit_date DATE,
    receipt_date DATE,
    ship_instruct VARCHAR(25),
    ship_mode VARCHAR(10),
    comment VARCHAR(44),

    PRIMARY KEY (order_id, line_number),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (supplierid) REFERENCES supplier(supplierid)
);