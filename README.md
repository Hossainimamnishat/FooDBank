A minimalistic, modular Food Delivery backend built with Django, DRF, PostgreSQL.

🚀 Features
🔐 Authentication

Register with Email / Phone

JWT Login

Role-based access control (Customer, Restaurant Owner, Driver, Admin)

👤 Customer Module

Customer profile

Multiple addresses (home/work/other)

Default address support

🍽️ Restaurant Module

Restaurant onboarding (licence, owner details, contact info)

Opening hours

Admin approval flow

Restaurant CRUD for owners

📋 Menus

Categories per restaurant

Menu items with ingredients, images, price, availability

Customer-facing menu browsing

🛒 Cart System

Cart per customer per restaurant

Add/update/remove items

Delivery or pickup mode

Suggest menu items

Auto-calculated subtotal, delivery fee, service fee

📦 Orders Module

Create orders from cart

Order status flow (pending → accepted → preparing → ready → delivered)

Restaurant order dashboard

Customer cancellation rules

Admin overview

🚗 Delivery Module

Driver profiles (bike/car)

Shifts (start/end, total hours worked)

Order assignment to drivers

Distance calculation (Haversine)

Per-km pay (0.15€ default)

Vehicle-specific distance limits (bike = 8 km, car = 15 km)

Driver order progression

💳 Payments Module

Simulated payment transactions

Payment status (pending / paid / refunded)

Full refunds
┌──────────────────────────┐
│        Frontend          │
│ (Mobile App / Web App)   │
└─────────────┬────────────┘
              │ REST API (JSON)
              ▼
┌──────────────────────────────────────────────────────────────┐
│                        Django Backend                         │
│                                                              │
│  ┌────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  Accounts  │   │  Customers    │   │   Restaurants     │   │
│  └────────────┘   └──────────────┘   └──────────────────┘   │
│          │                    │                  │           │
│  ┌────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │   Menus    │   │    Carts      │   │     Orders        │   │
│  └────────────┘   └──────────────┘   └──────────────────┘   │
│                     │                   │                    │
│            ┌────────┴───────┐     ┌────┴────────┐          │
│            │   Delivery     │     │   Payments   │          │
│            └────────────────┘     └──────────────┘          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
              │
              ▼
      ┌────────────────┐
      │  PostgreSQL    │
      └────────────────┘
| Role                 | Access                                        |
| -------------------- | --------------------------------------------- |
| **Customer**         | Cart, orders, payments                        |
| **Restaurant Owner** | Manage restaurant, menus, orders              |
| **Driver**           | Shifts, delivery assignments                  |
| **Admin**            | Approvals, global views, refunds, commissions |

Commission calculation per order

Admin dashboards for transactions, refunds, commissions
