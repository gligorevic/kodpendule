"""Fill Serbian (Latin) msgstr in locale/sr/LC_MESSAGES/django.po."""
from __future__ import annotations

import sys
from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parents[1]
PO_PATH = ROOT / "locale" / "sr" / "LC_MESSAGES" / "django.po"

# English msgid -> Serbian (Latin) msgstr
TRANSLATIONS: dict[str, str] = {
    'Archived': 'Arhivirano',
    'Archived products are hidden from the shop and cannot be purchased. Clear this option to restore them.': 'Arhivirani proizvodi su skriveni u prodavnici i ne mogu da se kupe. Isključite ovu opciju da ih vratite.',
    'Image source URL': 'URL izvora slike',
    'Image attribution': 'Autor i zasluge za sliku',
    'Image license URL': 'URL licence slike',
    'Product image': 'Slika proizvoda',
    'Optional source, author and license details shown below the main product image.': 'Opcioni podaci o izvoru, autoru i licenci prikazuju se ispod glavne slike proizvoda.',
    'Image source': 'Izvor slike',
    'Image license': 'Licenca slike',
    'Inventory XML': 'XML stanje artikala',
    'StanjeArtikalaWeb XML, up to 5 MB, UTF-8 or Windows-1250.': 'StanjeArtikalaWeb XML, do 5 MB, UTF-8 ili Windows-1250.',
    'Upload a non-empty XML file up to 5 MB.': 'Otpremite XML datoteku sa sadržajem, do 5 MB.',
    'Choose a category': 'Izaberite kategoriju',
    'Import inventory XML': 'Uvoz XML stanja artikala',
    'Category choices saved. Continue reviewing or apply the import.': 'Kategorije su sačuvane. Nastavite pregled ili primenite uvoz.',
    'Inventory imported: %(created)s new, %(updated)s updated, %(unchanged)s unchanged, %(rejected)s excluded.': 'Uvoz završen: %(created)s novih, %(updated)s ažuriranih, %(unchanged)s bez izmene, %(rejected)s izuzetih.',
    'Invalid import action.': 'Neispravna radnja uvoza.',
    'Barcode': 'Barkod',
    'Restricted product — excluded from import.': 'Artikal sa ograničenjem — izuzet iz uvoza.',
    'Invalid number in %(field)s.': 'Neispravan broj u polju %(field)s.',
    'Use UTF-8 or Windows-1250 XML encoding.': 'Koristite XML sa UTF-8 ili Windows-1250 kodiranjem.',
    'The XML encoding is invalid.': 'XML kodiranje nije ispravno.',
    'XML documents with DTD or entities are not allowed.': 'XML dokumenti sa DTD deklaracijama ili entitetima nisu dozvoljeni.',
    'The XML document is malformed.': 'XML dokument nije ispravno formiran.',
    'Expected ArtikliWeb with artikal records.': 'Očekuje se ArtikliWeb sa zapisima artikal.',
    'The XML must contain between 1 and 10,000 records.': 'XML mora da sadrži između 1 i 10.000 zapisa.',
    'Duplicate SKU %(sku)s. Correct the XML before importing.': 'Šifra %(sku)s je duplirana. Ispravite XML pre uvoza.',
    'Missing or overlong SKU, name or barcode.': 'Šifra, naziv ili barkod nedostaje ili je predugačak.',
    'Each record must have one name, price and quantity.': 'Svaki zapis mora imati tačno jedan naziv, cenu i količinu.',
    'Price exceeds the supported limit.': 'Cena prelazi podržanu granicu.',
    'Stock must be a non-negative whole number within the supported limit.': 'Stanje mora biti nenegativan ceo broj u okviru podržane granice.',
    'Barcode belongs to another SKU. Verify product identity before importing.': 'Barkod pripada drugoj šifri. Proverite identitet artikla pre uvoza.',
    'SKU matches a different product name or barcode. Verify product identity before importing.': 'Šifra odgovara drugom nazivu ili barkodu. Proverite identitet artikla pre uvoza.',
    'This preview has expired. Upload the XML again.': 'Ovaj pregled je istekao. Ponovo otpremite XML.',
    'This import has already been applied.': 'Ovaj uvoz je već primenjen.',
    'Invalid category selection.': 'Neispravan izbor kategorije.',
    'Choose an active category for every new product.': 'Izaberite aktivnu kategoriju za svaki novi artikal.',
    'Products changed during import. Upload the XML again.': 'Artikli su promenjeni tokom uvoza. Ponovo otpremite XML.',
    'Confirm that the excluded records will be skipped.': 'Potvrdite da će izuzeti zapisi biti preskočeni.',
    'There are no valid records to import.': 'Nema ispravnih zapisa za uvoz.',
    'Products changed after this preview. Upload the XML again; no changes were applied.': 'Artikli su promenjeni nakon pregleda. Ponovo otpremite XML; nijedna izmena nije primenjena.',
    'A restricted product was detected. Upload the XML again.': 'Otkriven je artikal sa ograničenjem. Ponovo otpremite XML.',
    'Match by SKU and verify product identity. Existing products: update stock only when it differs. Prices, descriptions, images and categories stay unchanged. Products missing from the XML stay unchanged.': 'Artikli se povezuju po šifri uz proveru identiteta. Postojećim artiklima menja se samo stanje, ako se razlikuje. Cene, opisi, slike i kategorije ostaju isti. Artikli kojih nema u XML-u ostaju nepromenjeni.',
    'New products require a category and use the XML name, barcode and price. Invalid or restricted records are excluded and listed for review.': 'Za nove artikle izaberite kategoriju; naziv, barkod i cena preuzimaju se iz XML-a. Neispravni zapisi i artikli sa ograničenjem izuzeti su i navedeni za pregled.',
    'Drag your XML file here or choose a file': 'Prevucite XML datoteku ovde ili izaberite datoteku',
    'Preview import': 'Pregledaj uvoz',
    'Recent imports': 'Skorašnji uvozi',
    'Applied': 'Primenjeno',
    'Preview': 'Pregled',
    'Total records': 'Ukupno zapisa',
    'New': 'Novo',
    'Stock changes': 'Izmene stanja',
    'Unchanged': 'Bez izmene',
    'Excluded': 'Izuzeto',
    'Import applied': 'Uvoz je primenjen',
    'Preview expires': 'Pregled ističe',
    'If the catalog or stock changes after preview, upload the XML again.': 'Ako se katalog ili stanje promene nakon pregleda, ponovo otpremite XML.',
    'New products still needing a category': 'Novi artikli bez izabrane kategorije',
    'Adding new products requires the add-product permission.': 'Za nove artikle potrebna je dozvola za dodavanje proizvoda.',
    'Show new products': 'Prikaži nove artikle',
    'Show all valid records': 'Prikaži sve ispravne zapise',
    'Upload another XML': 'Otpremi drugi XML',
    'Current stock': 'Trenutno stanje',
    'XML stock': 'Stanje iz XML-a',
    'XML price': 'Cena iz XML-a',
    'Action / category': 'Radnja / kategorija',
    'Created': 'Kreirano',
    'Update stock': 'Ažuriraj stanje',
    'No change': 'Bez izmene',
    'No records in this view.': 'Nema zapisa u ovom prikazu.',
    'Save categories on this page': 'Sačuvaj kategorije na ovoj strani',
    'Excluded records and reasons': 'Izuzeti zapisi i razlozi',
    'Record': 'Zapis',
    'Reason': 'Razlog',
    'I reviewed the excluded records and agree to skip them.': 'Pregledao/la sam izuzete zapise i prihvatam da se preskoče.',
    'Save category choices before applying. All valid changes are applied together.': 'Sačuvajte izbor kategorija pre primene. Sve ispravne izmene primenjuju se zajedno.',
    'Apply inventory import': 'Primeni uvoz stanja',
    "order": "Narudžbina",
    "Order": "Narudžbina",
    "Add order": "Dodaj narudžbinu",
    "Select order to change": "Izaberite narudžbinu za izmenu",
    "Select product to change": "Izaberite proizvod za izmenu",
    "Select category to change": "Izaberite kategoriju za izmenu",
    "Select city to change": "Izaberite grad za izmenu",
    "Select shipping method to change": "Izaberite način dostave za izmenu",
    "Select customer contact to change": "Izaberite kontakt kupca za izmenu",
    "Select group to change": "Izaberite grupu za izmenu",
    "Select user to change": "Izaberite korisnika za izmenu",
    "Add product": "Dodaj proizvod",
    "Add category": "Dodaj kategoriju",
    "Add city": "Dodaj grad",
    "Add shipping method": "Dodaj način dostave",
    "Add customer contact": "Dodaj kontakt kupca",
    "Add group": "Dodaj grupu",
    "Add user": "Dodaj korisnika",
    "Period type": "Tip perioda",
    "Quick overview": "Brzi pregled",
    "Manual period": "Ručni period",
    "From date": "Od datuma",
    "To date": "Do datuma",
    "Apply filter": "Primeni filter",
    "Customer profile": "Profil kupca",
    "Customer profiles": "Profili kupaca",
    "customer contact": "Kontakt kupca",
    "customer contacts": "Kontakti kupaca",
    "Customer contacts": "Kontakti kupaca",
    "Export CSV": "Izvezi CSV",
    "Export selected to CSV": "Izvezi izabrane u CSV",
    "No customers selected.": "Nije izabran nijedan kupac.",
    "No orders selected.": "Nije izabrana nijedna narudžbina.",
    "Delivery street": "Ulica i broj dostave",
    "Delivery city": "Grad dostave",
    "New (unread)": "Nova (nepročitana)",
    "Marked as read when opened in admin.": "Označava se kao pročitana kada je otvorite u adminu.",
    "Import CSV": "Uvezi CSV",
    "Import customer contacts": "Uvoz kontakata kupaca",
    "Upload a CSV file to create or update customer contacts by email. Rows with an existing email are updated; new emails are added.": "Otpremite CSV da kreirate ili ažurirate kontakte kupaca po emailu. Postojeći email se ažurira; novi se dodaje.",
    "Columns": "Kolone",
    "Download current data as CSV": "Preuzmi trenutne podatke kao CSV",
    "CSV file": "CSV datoteka",
    "UTF-8 CSV with a header row. Required column: email.": "UTF-8 CSV sa zaglavljem. Obavezna kolona: email.",
    "Import finished: %(created)s created, %(updated)s updated, %(skipped)s skipped.": "Uvoz završen: %(created)s novo, %(updated)s ažurirano, %(skipped)s preskočeno.",
    "Contact & delivery": "Kontakt i dostava",
    "User account": "Korisnički nalog",
    "Orders placed": "Broj narudžbina",
    "Registered at": "Registrovan",
    "First seen": "Prvi kontakt",
    "Last activity": "Poslednja aktivnost",
    "Account": "Nalog",
    "Addresses": "Adrese",
    "Username": "Korisničko ime",
    "Password": "Lozinka",
    "Subscribe to newsletter": "Prijavite se na bilten",
    "Welcome, %(name)s! Your account has been created.": "Dobrodošli, %(name)s! Vaš nalog je kreiran.",
    "You have been signed out.": "Odjavljeni ste.",
    "Product not found.": "Proizvod nije pronađen.",
    "This product is out of stock.": "Ovaj proizvod nije na zalihi.",
    "Not enough items in stock.": "Nema dovoljno na zalihi.",
    "“%(name)s” added to cart.": "„%(name)s” je dodat u korpu.",
    "Cart updated.": "Korpa je ažurirana.",
    "Item removed from cart.": "Stavka je uklonjena iz korpe.",
    "Browse product categories.": "Pregledajte kategorije proizvoda.",
    "Category not found.": "Kategorija nije pronađena.",
    "Select city": "Izaberite grad",
    "Street and number": "Ulica i broj",
    "Billing address is the same as shipping": "Adresa za naplatu je ista kao za dostavu",
    "Billing city": "Grad za naplatu",
    "Order note": "Napomena",
    "Optional — tell us anything we should know about delivery.": "Opciono — napišite sve što treba da znamo o dostavi.",
    "Order notes (required)": "Napomene uz narudžbinu (obavezno)",
    "Delivery instructions, building entrance, etc. (optional)": "Uputstva za dostavu, ulaz u zgradu itd. (opciono)",
    "Promotional delivery price applied to your order.": "Primenjena je promotivna cena dostave.",
    "Reduced delivery price applied to your order.": "Primenjena je snižena cena dostave.",
    "Add __AMOUNT__ RSD more to qualify for promotional delivery.": "Dodajte još __AMOUNT__ RSD za promotivnu dostavu.",
    "Free shipping threshold": "Prag vrednosti korpe",
    "Cart total threshold": "Prag vrednosti korpe",
    "When threshold is reached": "Kada je prag dostignut",
    "Discounted shipping price": "Snižena cena dostave",
    "Free shipping": "Besplatna dostava",
    "Promotional delivery": "Promotivna dostava",
    "Payment settings": "Podešavanja plaćanja",
    "Delivery city": "Grad za dostavu",
    "Configure promotional delivery rules separately for each city where you deliver.": (
        "Podesite promotivna pravila dostave posebno za svaki grad u kome vršite dostavu."
    ),
    "Promotional delivery rules per city": "Promotivna pravila dostave po gradu",
    "Payment settings saved for %(city)s.": "Podešavanja plaćanja su sačuvana za %(city)s.",
    "Add at least one active delivery city before configuring payment rules.": (
        "Dodajte bar jedan aktivan grad za dostavu pre podešavanja pravila plaćanja."
    ),
    "Enter a discounted delivery price for this mode.": (
        "Unesite sniženu cenu dostave za ovaj režim."
    ),
    "Back to top": "Nazad na vrh",
    "When the cart subtotal reaches the threshold, delivery cost is calculated automatically at checkout.": (
        "Kada ukupna vrednost korpe dostigne prag, cena dostave se automatski obračunava pri plaćanju."
    ),
    "Free shipping sets delivery to 0 RSD. Discounted uses the price below.": (
        "Besplatna dostava postavlja cenu na 0 RSD. Snižena koristi cenu ispod."
    ),
    "When the cart subtotal is at or above this amount (RSD), the threshold shipping rule below applies. Leave empty to disable.": (
        "Kada je ukupna vrednost korpe jednaka ili veća od ovog iznosa (RSD), primenjuje se pravilo ispod. Ostavite prazno da isključite."
    ),
    "When the cart subtotal is at or above this amount (RSD), the promotional delivery rule below applies. Leave empty to disable.": (
        "Kada je ukupna vrednost korpe jednaka ili veća od ovog iznosa (RSD), primenjuje se pravilo ispod. Ostavite prazno da isključite."
    ),
    "Cities": "Gradovi",
    "Choose free delivery or the discounted shipping price configured below.": (
        "Izaberite besplatnu dostavu ili sniženu cenu dostave ispod."
    ),
    "Used when threshold is reached and mode is “Discounted shipping price”. Leave empty if you only use free shipping.": (
        "Koristi se kada je prag dostignut i režim je „Snižena cena dostave“. Ostavite prazno ako koristite samo besplatnu dostavu."
    ),
    "Daily revenue": "Dnevni prihod",
    "Monthly revenue": "Mesečni prihod",
    "Daily orders": "Dnevne narudžbine",
    "Monthly orders": "Mesečne narudžbine",
    "Optional note from checkout.": "Opciona napomena sa plaćanja.",
    "Note": "Napomena",
    "Preferred delivery date": "Željeni datum dostave",
    "When should we deliver?": "Kada želite dostavu?",
    "Choose any date after today — delivery is free for scheduled orders.": "Izaberite bilo koji datum posle danas — dostava je besplatna za zakazane narudžbine.",
    "Choose a delivery date.": "Izaberite datum dostave.",
    "Choose a date after today for free scheduled delivery.": "Izaberite datum posle danas za besplatnu zakazanu dostavu.",
    "Deliver today (as soon as possible)": "Dostava danas ( što pre moguće )",
    "Schedule for a later date": "Zakaži za kasniji datum",
    "Requested delivery date": "Traženi datum dostave",
    "Customer's preferred delivery date from checkout.": "Traženi datum dostave koji je kupac izabrao pri plaćanju.",
    "Requested delivery date: %(date)s": "Traženi datum dostave: %(date)s",
    "Requested delivery date:": "Traženi datum dostave:",
    "Free delivery for your selected date.": "Besplatna dostava za izabrani datum.",
    "Delivery date": "Datum dostave",
    "Same-day delivery has a fee. Scheduling for a later date is free.": "Dostava istog dana se naplaćuje. Zakazivanje za kasniji datum je besplatno.",
    "Standard delivery fee applies.": "Primeni se standardna cena dostave.",
    "Free delivery — pick a future date below.": "Besplatna dostava — izaberite budući datum ispod.",
    "I am flexible with the delivery date": "Fleksibilan/sam sam oko datuma dostave",
    "Email is required for guest checkout.": "Email je obavezan za kupovinu kao gost.",
    "Email is required for checkout.": "Email je obavezan za završetak kupovine.",
    "Order confirmations are sent here. Use the recipient's email if you are ordering for someone else.": "Potvrde narudžbine šaljemo na ovu adresu. Unesite email primaoca ako naručujete za nekog drugog.",
    "Email is required.": "Email je obavezan.",
    "Required for order confirmations and signing in.": "Obavezan za potvrde narudžbina i prijavu.",
    "A user with that email already exists.": "Korisnik sa tim emailom već postoji.",
    "This email is already linked to another account.": "Ovaj email je već povezan sa drugim nalogom.",
    "Delivery date must be at least tomorrow.": "Datum dostave mora biti najkasnije od sutra.",
    "Order notes are required.": "Napomene uz narudžbinu su obavezne.",
    "This field is required.": "Ovo polje je obavezno.",
    "Your cart is empty.": "Vaša korpa je prazna.",
    "Open cart": "Otvori korpu",
    "Browse main categories and their subcategories.": "Pregledajte glavne kategorije i njihove podkategorije.",
    "Choose a category to explore.": "Izaberite kategoriju za pregled.",
    "Delivery is not available yet. Please contact us.": "Dostava još nije dostupna. Kontaktirajte nas.",
    "Thank you! Your order %(number)s has been placed.": "Hvala! Vaša narudžbina %(number)s je primljena.",
    "Order confirmed": "Narudžbina potvrđena",
    "Customers": "Kupci",
    "Contact": "Kontakt",
    "Reporting period: <strong>%(label)s</strong>": "Period izveštaja: <strong>%(label)s</strong>",
    "Category": "Kategorija",
    "Order item": "Stavka narudžbine",
    "Order items": "Stavke narudžbine",
    "Email address": "Email adresa",
    "Not enough stock for %(name)s.": "Nema dovoljno zaliha za %(name)s.",
    "Track your order": "Pratite narudžbinu",
    "We could not find an order with these details. Check the order number and email, then try again.": "Nismo pronašli narudžbinu sa ovim podacima. Proverite broj narudžbine i email, pa pokušajte ponovo.",
    "Order %(number)s": "Narudžbina %(number)s",
    "My orders": "Moje narudžbine",
    "Search results for “%(query)s”": "Rezultati pretrage za „%(query)s”",
    "Browse our product catalog.": "Pregledajte naš katalog proizvoda.",
    "Browse products on promo sale.": "Pregledajte proizvode na promo akciji.",
    "Browse our recommended products.": "Pregledajte naše preporučene proizvode.",
    "Products on special offer — prices marked down for a limited time.": "Proizvodi na specijalnoj ponudi — snižene cene u ograničenom periodu.",
    "Products we highlight for you — hand-picked in the admin.": "Proizvodi koje ističemo za vas — ručno izabrani u administraciji.",
    "Prijava": "Prijava",
    "Sign in to track orders and save addresses.": "Prijavite se da pratite narudžbine i sačuvate adrese.",
    "Guest checkout does not require an account.": "Kupovina kao gost ne zahteva nalog.",
    "Sign in": "Prijava",
    "No account?": "Nemate nalog?",
    "Register": "Registracija",
    "Registracija": "Registracija",
    "Create an account to track orders and save your details.": "Napravite nalog da pratite narudžbine i sačuvate podatke.",
    "Create account": "Kreiraj nalog",
    "Already have an account?": "Već imate nalog?",
    "No recent changes yet.": "Još nema skorašnjih izmena.",
    "Serbian": "Srpski",
    "English": "Engleski",
    "%(field)s (%(language)s)": "%(field)s (%(language)s)",
    "Alt text (Serbian)": "Alt tekst (srpski)",
    "Alt text (English)": "Alt tekst (engleski)",
    "Name (Serbian)": "Naziv (srpski)",
    "Name (English)": "Naziv (engleski)",
    "Description (Serbian)": "Opis (srpski)",
    "Description (English)": "Opis (engleski)",
    "Enter Serbian and English for each field. Name is shown on the shop; slug is used in the URL.": (
        "Unesite srpski i engleski za svako polje. Naziv se prikazuje u prodavnici; "
        "slug se koristi u URL-u."
    ),
    "Filter navigation items": "Filtriraj stavke menija",
    "Kod Pendule": "Kod Pendule",
    "Update": "Ažuriraj",
    "OK": "U redu",
    "Shipping is calculated at checkout.": "Dostava se obračunava pri plaćanju.",
    "Proceed to checkout": "Nastavi na plaćanje",
    "Continue shopping": "Nastavi kupovinu",
    "Browse products": "Pregledaj proizvode",
    "Subcategories": "Podkategorije",
    "No image": "Nema slike",
    "No categories available yet.": "Još nema dostupnih kategorija.",
    "You can checkout as a guest — no account required.": "Možete kupiti kao gost — nalog nije potreban.",
    "or": "ili",
    "register": "registracija",
    "Shipping address": "Adresa za dostavu",
    "Delivery address": "Adresa za dostavu",
    "Billing address": "Adresa za naplatu",
    "Same as shipping": "Isto kao za dostavu",
    "Delivery": "Dostava",
    "Payment: cash on delivery.": "Plaćanje: pouzećem.",
    "cash on delivery": "pouzećem",
    "Cash on delivery": "Plaćanje pouzećem",
    "Pay on delivery": "Plaćanje pouzećem",
    "Pay on delivery — pay when your package arrives.": "Plaćanje pouzećem — platite kada paket stigne.",
    "Payment: cash on delivery when the order is delivered.": "Plaćanje: pouzećem pri isporuci narudžbine.",
    "Cash on delivery — pay when your order arrives.": "Plaćanje pouzećem — platite kada narudžbina stigne.",
    "Place order": "Poruči",
    "Please correct the highlighted fields and try again.": "Ispravite označena polja i pokušajte ponovo.",
    "We could not place your order. Please try again or contact us.": "Narudžbina nije poslata. Pokušajte ponovo ili nas kontaktirajte.",
    "Some fields need your attention before we can place the order.": "Proverite polja pre slanja narudžbine.",
    "New order %(number)s": "Nova narudžbina %(number)s",
    "Your order %(number)s — Kod Pendule": "Vaša narudžbina %(number)s — Kod Pendule",
    "Thank you for your order! We have received it and will contact you "
    "if we need any additional information.": (
        "Hvala na narudžbini! Primili smo je i kontaktiraćemo vas ako nam "
        "zatreba dodatna informacija."
    ),
    "A new order has been placed on the shop.": "Nova narudžbina je poslata preko prodavnice.",
    "A new order was placed on the shop.": "Nova narudžbina je poslata preko prodavnice.",
    "Customer": "Kupac",
    "Name: %(name)s": "Ime: %(name)s",
    "Address: %(street)s": "Adresa: %(street)s",
    "City: %(city)s": "Grad: %(city)s",
    "Notes: %(notes)s": "Napomene: %(notes)s",
    "- %(name)s × %(qty)s @ %(unit)s = %(total)s": "- %(name)s × %(qty)s @ %(unit)s = %(total)s",
    "Subtotal: %(amount)s": "Ukupno: %(amount)s",
    "Shipping: %(amount)s": "Dostava: %(amount)s",
    "Total: %(amount)s": "Ukupno: %(amount)s",
    "Low stock: %(name)s": "Malo zaliha: %(name)s",
    "A product has reached the low-stock alert threshold.": (
        "Proizvod je dostigao prag upozorenja za niske zalihe."
    ),
    "Product: %(name)s": "Proizvod: %(name)s",
    "SKU: %(sku)s": "Šifra: %(sku)s",
    "Stock remaining: %(stock)s": "Preostalo na stanju: %(stock)s",
    "Alert threshold: %(threshold)s": "Prag upozorenja: %(threshold)s",
    "Contact form: %(name)s": "Kontakt forma: %(name)s",
    "A message was submitted via the shop contact form.": (
        "Poruka je poslata putem kontakt forme na sajtu."
    ),
    "Message:": "Poruka:",
    "Thank you! Your message has been sent. We will get back to you soon.": (
        "Hvala! Vaša poruka je poslata. Javićemo vam se uskoro."
    ),
    "We could not send your message right now. "
    "Please try again later or call us using the details below.": (
        "Poruka trenutno nije poslata. Pokušajte ponovo kasnije "
        "ili nas pozovite putem podataka ispod."
    ),
    "Order number: %(number)s": "Broj narudžbine: %(number)s",
    "Customer: %(name)s": "Kupac: %(name)s",
    "Email: %(email)s": "Email: %(email)s",
    "Phone: %(phone)s": "Telefon: %(phone)s",
    "Total: %(total)s": "Ukupno: %(total)s",
    "Delivery city: %(city)s": "Grad dostave: %(city)s",
    "Delivery street: %(street)s": "Ulica dostave: %(street)s",
    "Preferred delivery date: %(date)s": "Željeni datum dostave: %(date)s",
    "Order notes:": "Napomene uz narudžbinu:",
    "Order summary": "Pregled narudžbine",
    "Thank you for your order!": "Hvala na narudžbini!",
    "Your order number is <strong>%(number)s</strong>.": "Broj vaše narudžbine je <strong>%(number)s</strong>.",
    "We will contact you to confirm delivery. Payment on delivery (cash).": "Kontaktiraćemo vas radi potvrde dostave. Plaćanje pouzećem (gotovina).",
    "View order details": "Detalji narudžbine",
    "Track this order later": "Pratite ovu narudžbinu kasnije",
    "Save your order number and email — you will need both to track the order.": "Sačuvajte broj narudžbine i email — oba su potrebna za praćenje.",
    "Track order": "Prati narudžbinu",
    "Your order has been received.": "Vaša narudžbina je primljena.",
    "All products": "Svi proizvodi",
    "Shop": "Prodavnica",
    "Search products…": "Pretraži proizvode…",
    "Product gallery": "Galerija proizvoda",
    "Gallery thumbnails": "Sličice galerije",
    "Pricing": "Cena",
    "Delivery and payment": "Dostava i plaćanje",
    "Payment": "Plaćanje",
    "cash on delivery (COD)": "pouzećem",
    "calculated at checkout": "obračunava se pri plaćanju",
    "Support": "Podrška",
    "Decrease quantity": "Smanji količinu",
    "Increase quantity": "Povećaj količinu",
    "This product is currently out of stock.": "Ovaj proizvod trenutno nije na zalihi.",
    "More options in the same category.": "Više opcija u istoj kategoriji.",
    "View category": "Pogledaj kategoriju",
    "Sign out": "Odjava",
    "Open menu": "Otvori meni",
    "Open site menu": "Otvori meni sajta",
    "Close menu": "Zatvori meni",
    "Overview of sales, orders, and inventory. Open the menu button above to reach all sections.": (
        "Pregled prodaje, narudžbina i zaliha. Otvorite dugme menija iznad da biste pristupili svim sekcijama."
    ),
    "Main navigation": "Glavna navigacija",
    "Menu": "Meni",
    "Language": "Jezik",
    "Hello, %(name)s": "Zdravo, %(name)s",
    "Welcome": "Dobrodošli",
    "Discover quality products with reliable delivery across Serbia.": "Otkrijte kvalitetne proizvode uz pouzdanu dostavu širom Srbije.",
    "Serbian online store": "Srpska internet prodavnica",
    "A calm, trustworthy shopping experience — browse products, order securely, and pay on delivery.": "Mirno i pouzdano kupovanje — pregledajte proizvode, poručite bezbedno i platite pouzećem.",
    "Discover clocks, décor, and gifts with a calm checkout — order online and pay when your package arrives.": "Otkrijte satove, dekoracije i poklone uz jednostavnu kupovinu — poručite online i platite kada paket stigne.",
    "Order drinks and everyday essentials online — browse categories, checkout in minutes, and pay when your order arrives.": "Poručite pića i svakodnevne proizvode online — pregledajte kategorije, završite kupovinu za nekoliko minuta i platite kada narudžbina stigne.",
    "Order now": "Poruči odmah",
    "Fast delivery": "Brza dostava",
    "Reliable delivery across Serbia": "Pouzdana dostava širom Srbije",
    "No card required at checkout": "Kartica nije potrebna pri poručivanju",
    "Pick a category, add items to your cart, and complete checkout in a few steps.": "Izaberite kategoriju, dodajte proizvode u korpu i završite kupovinu u nekoliko koraka.",
    "Shop collection": "Pogledaj kolekciju",
    "Browse categories": "Pregledaj kategorije",
    "Products": "Proizvoda",
    "Categories": "Kategorija",
    "Pay on delivery": "Plaćanje pouzećem",
    "New season": "Nova sezona",
    "Curated pieces for every room": "Odabrani komadi za svaki prostor",
    "Free guidance": "Besplatne savete",
    "We help before & after purchase": "Pomažemo pre i posle kupovine",
    "Collections": "Kolekcije",
    "Just in": "Upravo stiglo",
    "New arrivals": "Novo u ponudi",
    "Fresh picks from our catalog — updated regularly.": "Sveži izbori iz kataloga — redovno ažurirano.",
    "About the shop": "O prodavnici",
    "Thoughtful pieces for everyday living": "Pažljivo odabrano za svakodnevni dom",
    "We select products that feel at home in Serbian households — reliable quality, honest pricing, and delivery you can count on.": "Biramo proizvode koji prirodno pripadaju domovima u Srbiji — pouzdan kvalitet, jasne cene i dostava na koju možete da računate.",
    "Hand-checked assortment": "Ručno proveren asortiman",
    "Clear product information": "Jasne informacije o proizvodu",
    "Support in Serbian": "Podrška na srpskom",
    "Talk to us": "Pišite nam",
    "Spotlight": "U fokusu",
    "Special offers": "Posebne ponude",
    "Simple process": "Jednostavan proces",
    "How shopping works": "Kako funkcioniše kupovina",
    "From browsing to doorstep — four clear steps.": "Od pregleda do vrata — četiri jasna koraka.",
    "Browse & choose": "Pregledaj i izaberi",
    "Explore categories or search the catalog for the right product.": "Istražite kategorije ili pretražite katalog za pravi proizvod.",
    "Add to cart": "Dodaj u korpu",
    "Review items and quantities before checkout — no account required for guests.": "Proverite stavke i količine pre plaćanja — nalog nije obavezan za goste.",
    "Enter delivery details and confirm your order in a few minutes.": "Unesite podatke za dostavu i potvrdite narudžbinu za nekoliko minuta.",
    "Receive your package and pay the courier in cash — track status anytime.": "Preuzmite paket i platite kurira gotovinom — status pratite uvek.",
    "Option to pay on site, by card or in cash.": "Mogućnost plaćanja na licu mesta, karticom i gotovinom.",
    "Pay by card": "Plaćanje karticom",
    "Pay in cash": "Plaćanje gotovinom",
    "Please select how you want to pay.": "Izaberite način plaćanja.",
    "Payment method: %(method)s": "Način plaćanja: %(method)s",
    "Our promise": "Naše obećanje",
    "Shop now": "Kupi sada",
    "Fast delivery": "Brza dostava",
    "More highlights": "Još istaknutih ponuda",
    "Slide": "Slajd",
    "Previous": "Prethodno",
    "Next": "Sledeće",
    "Shop by category": "Kupuj po kategoriji",
    "Find what you need faster — browse our main categories.": "Brže pronađite što vam treba — pregledajte glavne kategorije.",
    "All categories": "Sve kategorije",
    "Start shopping": "Počni kupovinu",
    "Ready to order?": "Spremni za porudžbinu?",
    "Browse the catalog, add items to your cart, and complete checkout in a few steps.": "Pregledajte katalog, dodajte u korpu i završite kupovinu u nekoliko koraka.",
    "View cart": "Pogledaj korpu",
    "Shop with confidence": "Kupujte sa poverenjem",
    "Clear process from browsing to delivery — designed for everyday customers in Serbia.": "Jasan proces od pregleda do isporuke — prilagođen kupcima u Srbiji.",
    "Secure ordering": "Bezbedna porudžbina",
    "Your details are handled carefully. Confirm your order before delivery — no surprises.": "Vaši podaci se pažljivo čuvaju. Potvrdite narudžbinu pre isporuke — bez iznenađenja.",
    "We prepare orders quickly and keep you informed about shipping and handover.": "Brzo pripremamo narudžbine i obaveštavamo vas o slanju i preuzimanju.",
    "Pay when the package arrives. Simple and familiar — ideal if you prefer not to pay online.": "Platite kada paket stigne. Jednostavno i poznato — idealno ako ne želite online plaćanje.",
    "Support & contact": "Podrška i kontakt",
    "Questions about products or your order? We are here to help.": "Pitanja o proizvodima ili narudžbini? Tu smo da pomognemo.",
    "Contact us": "Kontaktirajte nas",
    "Call us": "Pozovite nas",
    "Why shop with us": "Zašto kupovati kod nas",
    "Pay on delivery (COD)": "Plaćanje pouzećem",
    "Order tracking": "Praćenje narudžbine",
    "Recommended for you": "Preporučeno za vas",
    "Recommended products": "Preporučeni proizvodi",
    "Recommended product": "Preporučeni proizvod",
    "Recommended sort order": "Redosled preporuke",
    "Choose products for the homepage carousel": "Izaberite proizvode za početnu stranicu",
    "Check products to show in the “Recommended products” section on the homepage. Order follows the list below (top to bottom).": "Označite proizvode za sekciju „Preporučeni proizvodi” na početnoj. Redosled prati listu (odozgo nadole).",
    "Select all": "Izaberi sve",
    "Clear all": "Poništi izbor",
    "Recommended": "Preporučeno",
    "No products yet. Add products first, then mark them as recommended.": "Još nema proizvoda. Prvo dodajte proizvode, pa ih označite kao preporučene.",
    "Save recommended products": "Sačuvaj preporučene proizvode",
    "Recommended products updated (%(count)s selected).": "Preporučeni proizvodi su ažurirani (%(count)s izabrano).",
    "Staff picks": "Naš izbor",
    "Products we highlight for you — browse page by page.": "Proizvodi koje ističemo — listajte stranicu po stranicu.",
    "Products we highlight for you — swipe or use arrows to browse.": "Proizvodi koje ističemo — prevucite ili koristite strelice za pregled.",
    "Previous products": "Prethodni proizvodi",
    "Next products": "Sledeći proizvodi",
    "slide": "slajd",
    "Page %(num)s of %(total)s": "Strana %(num)s od %(total)s",
    "Go to page %(num)s": "Idi na stranu %(num)s",
    "Recommended product pages": "Stranice preporučenih proizvoda",
    "Limited offers — order while stock lasts.": "Ograničene ponude — poručite dok ima na zalihi.",
    "Hand-picked items our customers love.": "Ručno odabrani proizvodi koje kupci vole.",
    "Popular picks from our catalog.": "Popularni izbori iz našeg kataloga.",
    "View all": "Pogledaj sve",
    "Pagination": "Straničenje",
    "\n                    Page %(num)s of %(total)s\n                ": "\n                    Strana %(num)s od %(total)s\n                ",
    "Sale": "Akcija",
    "Out of stock": "Nema na zalihi",
    "No products found.": "Nema pronađenih proizvoda.",
    "Promotions": "Promocije",
    "Learn more": "Saznaj više",
    "Placed on %(date)s": "Poručeno %(date)s",
    "Items": "Stavke",
    "Preferred delivery: %(date)s": "Željena dostava: %(date)s",
    "Flexible": "Fleksibilno",
    "Notes:": "Napomene:",
    "Date": "Datum",
    "Details": "Detalji",
    "Orders pagination": "Straničenje narudžbina",
    "You have not placed any orders yet while signed in.": "Još niste poručili ništa dok ste prijavljeni.",
    "Guest order?": "Narudžbina kao gost?",
    "Track by order number": "Prati po broju narudžbine",
    "example: KP-123456": "primer: KP-123456",
    "This order has been cancelled.": "Ova narudžbina je otkazana.",
    "Payment on delivery (cash).": "Plaćanje pouzećem (gotovina).",
    "Enter the order number from your confirmation and the email address you used at checkout.": "Unesite broj narudžbine iz potvrde i email koji ste koristili pri kupovini.",
    "Find my order": "Pronađi moju narudžbinu",
    "Have an account?": "Imate nalog?",
    "to see all your orders.": "da vidite sve svoje narudžbine.",
    "Contact information": "Kontakt informacije",
    "Questions about products, delivery, or your order? Reach us using the details below.": (
        "Pitanja o proizvodima, dostavi ili porudžbini? Javite nam se putem podataka ispod."
    ),
    "Questions about products, delivery, or your order? Reach us using the details below or send us a message.": (
        "Pitanja o proizvodima, dostavi ili narudžbini? Javite nam se putem podataka ispod ili pošaljite poruku."
    ),
    "Questions about products, delivery, or your order? Write to us.": "Pitanja o proizvodima, dostavi ili narudžbini? Pišite nam.",
    "Send us a message": "Pošaljite nam poruku",
    "Your name": "Vaše ime",
    "Your email": "Vaš email",
    "Subject": "Naslov",
    "Message": "Poruka",
    "How can we help you?": "Kako vam možemo pomoći?",
    "Send message": "Pošaljite poruku",
    "Website": "Veb sajt",
    "Thank you! We received your message and will reply as soon as possible.": "Hvala! Primili smo vašu poruku i odgovorićemo vam u najkraćem roku.",
    "We could not send your message. Please try again later or call us.": "Poruka nije poslata. Pokušajte ponovo kasnije ili nas pozovite.",
    "Contact form: %(subject)s": "Kontakt forma: %(subject)s",
    "Name: %(name)s\nEmail: %(email)s\nSubject: %(subject)s\n\n%(message)s": (
        "Ime: %(name)s\n"
        "Email: %(email)s\n"
        "Naslov: %(subject)s\n\n"
        "%(message)s"
    ),
    "Knez Mihailova 1\n11000 Beograd": "Knez Mihailova 1\n11000 Beograd",
    "Karađorđeva 11\n22408 Vrdnik": "Karađorđeva 11\n22408 Vrdnik",
    "Mon–Fri: 9:00–17:00\nSat: 9:00–13:00": "Pon–Pet: 09:00–17:00\nSub: 09:00–13:00",
    "Featured product sections will appear here once configured in the admin.": "Istaknute sekcije proizvoda pojaviće se kada budu podešene u administraciji.",
    "In stock": "Na stanju",
    "Add to cart": "Dodaj u korpu",
    "More in": "Više u",
    "Related products": "Srodni proizvodi",
    "Search: %(query)s": "Pretraga: %(query)s",
    "Showing %(count)s products": "Prikazano %(count)s proizvoda",
    "Search…": "Pretraga…",
    "Apply": "Primeni",
    "Documentation": "Dokumentacija",
    "Change": "Izmeni",
    "Delete": "Obriši",
    "Save": "Sačuvaj",
    "Save and continue editing": "Sačuvaj i nastavi izmenu",
    "Save and add another": "Sačuvaj i dodaj još jedan",
    "Delete selected %(verbose_name_plural)s": "Obriši izabrane %(verbose_name_plural)s",
    "Filter": "Filter",
    "Go": "Primeni",
    "Action": "Akcija",
    "Actions": "Akcije",
    "Run": "Pokreni",
    "0 of %(total_count)s selected": "0 od %(total_count)s izabrano",
    "Select all %(total_count)s %(module_name)s": "Izaberi svih %(total_count)s — %(module_name)s",
    "Clear selection": "Poništi izbor",
    "Show all": "Prikaži sve",
    "Hide counts": "Sakrij brojeve",
    "Any date": "Bilo koji datum",
    "Today": "Danas",
    "Past 7 days": "Poslednjih 7 dana",
    "This month": "Ovaj mesec",
    "This year": "Ova godina",
    "No date": "Bez datuma",
    "Has date": "Ima datum",
    "Yes": "Da",
    "No": "Ne",
    "Unknown": "Nepoznato",
    "All": "Sve",
    "None": "Ništa",
    "Please correct the error below.": "Ispravite grešku ispod.",
    "Please correct the errors below.": "Ispravite greške ispod.",
    "Start typing to filter…": "Kucajte za filtriranje…",
    "Skip to main content": "Preskoči na glavni sadržaj",
    "Breadcrumbs": "Putanja",
    "Action flag": "Tip akcije",
    "Change message": "Poruka izmene",
    "Log entry": "Zapis u dnevniku",
    "Log entries": "Zapisi u dnevniku",
    "History": "Istorija",
    "Back": "Nazad",
    "Add another": "Dodaj još",
    "Results": "Rezultati",
    "full result list": "puna lista rezultata",
    "Site administration": "Administracija sajta",
    "Django administration": "Django administracija",
    "English": "Engleski",
    "Serbian": "Srpski",
    "Srpski": "Srpski",
    "Cart": "Korpa",
    "Checkout": "Plaćanje",
    "Products": "Proizvodi",
    "Categories": "Kategorije",
    "Search": "Pretraga",
    "Close": "Zatvori",
    "Remove": "Ukloni",
    "View": "Pregled",
    "Add": "Dodaj",
    "Welcome,": "Dobrodošli,",
    "View site": "Pogledaj sajt",
    "Change password": "Promeni lozinku",
    "Log out": "Odjava",
    "Show counts": "Prikaži brojeve",
    "Select action": "Izaberite akciju",
    "No results found.": "Nema rezultata.",
    "Toggle navigation": "Prikaži/sakrij meni",
    "Sidebar": "Bočni meni",
    "Date/time": "Datum/vreme",
    "User": "Korisnik",
    "Users": "Korisnici",
    "Registered": "Registrovan",
    "Customer contact": "Kontakt kupca",
    "Ordering": "Redosled",
    # Cart & checkout (Frontend Phase 6)
    "SKU": "Šifra",
    "Line total": "Ukupno za stavku",
    "Your cart is empty": "Vaša korpa je prazna",
    "Browse our catalog and add products you like — checkout is simple and secure.": "Pregledajte katalog i dodajte proizvode — plaćanje je jednostavno i bezbedno.",
    "Cart items": "Stavke u korpi",
    "Cash on delivery — simple and secure.": "Plaćanje pouzećem — jednostavno i bezbedno.",
    "We will use these details to confirm your order.": "Koristićemo ove podatke da potvrdimo narudžbinu.",
    "Where should we deliver your order?": "Gde želite da dostavimo narudžbinu?",
    "Delivery cost for selected city": "Cena dostave za izabrani grad",
    "Tell us when and how you prefer delivery.": "Recite nam kada i kako želite dostavu.",
    "Cash on delivery (COD)": "Plaćanje pouzećem",
    "Pay the courier in cash when your order arrives. No online payment or card required.": "Platite kuriru gotovinom kada paket stigne. Nije potrebno online plaćanje ni kartica.",
    "Payment is available in cash or by card when you receive your order.": "Plaćanje je moguće gotovinom ili karticom prilikom preuzimanja robe.",
    "By placing the order you confirm your details are correct.": "Poručivanjem potvrđujete da su podaci tačni.",
    "Estimated total": "Ukupno",
    "Payment: cash on delivery (COD) when the order is delivered.": "Plaćanje: pouzećem pri isporuci narudžbine.",
    "No items in cart.": "Nema stavki u korpi.",
    "Secure ordering — your details are handled carefully.": "Bezbedna porudžbina — vaši podaci se pažljivo čuvaju.",
    "Fast delivery — we prepare orders quickly.": "Brza dostava — brzo pripremamo narudžbine.",
    "Pay on delivery (COD) — pay when your package arrives.": "Plaćanje pouzećem — platite kada paket stigne.",
    "Questions? Contact us anytime.": "Pitanja? Kontaktirajte nas u bilo kom trenutku.",
    "What happens next": "Šta sledi",
    "We review your order and prepare it for delivery.": "Pregledamo narudžbinu i pripremamo je za dostavu.",
    "We call or message you to confirm the delivery time.": "Zovemo vas ili šaljemo poruku da potvrdimo vreme dostave.",
    "Pay the courier in cash when your package arrives.": "Platite kuriru gotovinom kada paket stigne.",
    "Your order number is <span class=\"shop-order-success__number\">%(number)s</span>.": "Broj vaše narudžbine je <span class=\"shop-order-success__number\">%(number)s</span>.",
    "Subtotal": "Ukupno",
    "Items total": "Ukupno",
    "Shipping": "Dostava",
    "Quantity": "Količina",
    # Footer (Frontend Phase 7)
    "Customer service": "Korisnička podrška",
    "Contact & delivery": "Kontakt i dostava",
    "Quality products and reliable delivery across Serbia — order online, pay on delivery.": "Kvalitetni proizvodi i pouzdana dostava širom Srbije — poručite online, platite pouzećem.",
    "Quality products and reliable delivery — order online, pay on delivery.": "Kvalitetni proizvodi i pouzdana dostava — poručite online, platite pouzećem.",
    "Carefully selected assortment and transparent pricing.": "Pažljivo odabran asortiman i jasne cene.",
    "Nationwide delivery — shipping cost is shown at checkout.": "Dostava širom Srbije — cena dostave se prikazuje pri plaćanju.",
    "All rights reserved.": "Sva prava zadržana.",
    "Cash on delivery (COD) — pay when your order arrives.": "Plaćanje pouzećem — platite kada narudžbina stigne.",
    "Phone": "Telefon",
    "Email": "Email",
    "Address": "Adresa",
    "Working hours": "Radno vreme",
    # Polish (Frontend Phase 9)
    "Try another category or adjust your search.": "Probajte drugu kategoriju ili prilagodite pretragu.",
    "Browse all products": "Pregledaj sve proizvode",
    # Promo sales admin (Phase 10)
    "Promo sales": "Promo akcije",
    "Apply discounts to multiple products": "Primeni popuste na više proizvoda",
    "Products": "Proizvodi",
    "Pricing mode": "Način određivanja cene",
    "Lower by percentage": "Smanji za procenat",
    "Set fixed promo price": "Postavi fiksnu promo cenu",
    "Discount percent": "Procenat popusta",
    "Example: 15 means 15% discount from regular price.": "Primer: 15 znači 15% popusta na redovnu cenu.",
    "Fixed promo price": "Fiksna promo cena",
    "Set one promo price for all selected products.": "Postavite jednu promo cenu za sve izabrane proizvode.",
    "Mark products as on sale": "Označi proizvode kao na akciji",
    "Enter discount percent.": "Unesite procenat popusta.",
    "Enter fixed promo price.": "Unesite fiksnu promo cenu.",
    "Promo sale updated for %(count)s products.": "Promo akcija je ažurirana za %(count)s proizvoda.",
    "%(count)s products skipped because promo price was not lower than regular price.": "%(count)s proizvoda je preskočeno jer promo cena nije niža od redovne cene.",
    "Select products and apply a percentage discount or a fixed promo price.": "Izaberite proizvode i primenite procentualni popust ili fiksnu promo cenu.",
    "Select products and apply a percentage discount from the regular price.": "Izaberite proizvode i primenite procentualni popust od redovne cene.",
    "Apply promo sale": "Primeni promo akciju",
    "Remove promo from selected": "Ukloni promo sa izabranih",
    "Promo removed from %(count)s products.": "Promo uklonjen sa %(count)s proizvoda.",
    "No products selected.": "Nijedan proizvod nije izabran.",
    "None of the selected products had an active promo price.": "Nijedan izabrani proizvod nema aktivnu promo cenu.",
    "Enter a discount percent to apply a promo sale.": "Unesite procenat popusta da biste primenili promo akciju.",
    "Select products, then apply a percentage discount or remove the promo price. Products with a promo price appear in the homepage promo section.": "Izaberite proizvode, zatim primenite procenat popusta ili uklonite promo cenu. Proizvodi sa promo cenom se prikazuju u promo sekciji na početnoj.",
    "Select on promo": "Izaberi na akciji",
    "Select": "Izaberi",
    "Promo price": "Promo cena",
    "Regular price": "Redovna cena",
    "No products yet. Add products first, then set promo prices.": "Još nema proizvoda. Prvo dodajte proizvode, pa postavite promo cene.",
    "Cancel": "Otkaži",
    "Promo sale": "Promo akcija",
    "Limited-time discounts on selected products.": "Ograničeni popusti na izabrane proizvode.",
    "Limited-time discounts — swipe or use arrows to browse.": "Ograničeni popusti — prevucite ili koristite strelice za pregled.",
    # Legal / privacy (storefront compliance)
    "Terms of Service": "Uslovi korišćenja",
    "Privacy Policy": "Politika privatnosti",
    "Legal": "Pravne informacije",
    "Legal consent": "Pravna saglasnost",
    "I have read and accept the": "Pročitao/la sam i prihvatam",
    "and": "i",
    "I have read and accept the Terms of Service and Privacy Policy.": (
        "Pročitao/la sam i prihvatam Uslove korišćenja i Politiku privatnosti."
    ),
    "You must accept the Terms of Service and Privacy Policy to place an order.": (
        "Morate prihvatiti Uslove korišćenja i Politiku privatnosti da biste poručili."
    ),
    "Store location on map": "Lokacija prodavnice na mapi",
    "Last updated: June 2026": "Poslednje ažuriranje: jun 2026.",
    "1. Data controller": "1. Rukovalac podacima",
    "Controller:": "Rukovalac:",
    "2. What data we collect": "2. Koje podatke prikupljamo",
    "Identity and contact data: name, email, phone, delivery address.": (
        "Identitet i kontakt: ime, email, telefon, adresa dostave."
    ),
    "Order data: products ordered, amounts, payment method (cash on delivery), order notes, order number.": (
        "Podaci o narudžbini: proizvodi, iznosi, način plaćanja (pouzeće), napomene, broj narudžbine."
    ),
    "Account data (if you register): username, email, password (stored hashed), order history link.": (
        "Podaci naloga (ako se registrujete): korisničko ime, email, lozinka (heširana), istorija narudžbina."
    ),
    "Contact form: name, email, optional phone, message content.": (
        "Kontakt forma: ime, email, opcioni telefon, sadržaj poruke."
    ),
    "Technical data: IP address, browser type, and logs needed for security and operation.": (
        "Tehnički podaci: IP adresa, tip pregledača i logovi potrebni za bezbednost i rad sajta."
    ),
    "3. Purposes and legal bases": "3. Svrhe i pravni osnovi",
    "Purpose": "Svrha",
    "Legal basis": "Pravni osnov",
    "Processing and delivering orders": "Obrada i isporuka narudžbina",
    "Performance of a contract; legal obligation (tax/accounting records)": (
        "Izvršenje ugovora; zakonska obaveza (poreski/knjigovodstveni zapisi)"
    ),
    "Customer accounts and order history": "Korisnički nalozi i istorija narudžbina",
    "Contract; legitimate interest (customer service)": (
        "Ugovor; legitimni interes (korisnička podrška)"
    ),
    "Contact form and customer support": "Kontakt forma i podrška kupcima",
    "Legitimate interest; pre-contractual steps at your request": (
        "Legitimni interes; predugovorne radnje na vaš zahtev"
    ),
    "Order and low-stock email notifications": "Email obaveštenja o narudžbini i niskim zalihama",
    "Contract; legitimate interest (shop operations)": (
        "Ugovor; legitimni interes (poslovanje prodavnice)"
    ),
    "Website security, session, and language preference": (
        "Bezbednost sajta, sesija i izbor jezika"
    ),
    "Legitimate interest; consent where required": (
        "Legitimni interes; saglasnost gde je potrebna"
    ),
    "4. Customer accounts": "4. Korisnički nalozi",
    "When you register, we store the data needed to identify you and link your orders. You may update your profile through the account area where available. You can request account deletion by contacting us; we may retain certain order records as required by law.": (
        "Pri registraciji čuvamo podatke potrebne za identifikaciju i povezivanje narudžbina. "
        "Profil možete ažurirati u nalogu gde je dostupno. Brisanje naloga zatražite putem kontakta; "
        "određene zapise o narudžbinama možemo zadržati u skladu sa zakonom."
    ),
    "5. Orders": "5. Narudžbine",
    "Order data is used to fulfil the contract, communicate about delivery, prevent fraud, and maintain business records. We share delivery details with our logistics partners only to the extent necessary to deliver your package.": (
        "Podatke o narudžbini koristimo za izvršenje ugovora, komunikaciju o dostavi, sprečavanje zloupotrebe "
        "i poslovnu evidenciju. Podatke za dostavu delimo sa kurirskim partnerima samo u neophodnoj meri."
    ),
    "6. Contact forms": "6. Kontakt forme",
    "Messages you send via the contact form are delivered to our shop email inbox. We use your email to reply. Do not send sensitive health or financial data unless necessary. Spam protection (honeypot) may be used without profiling you.": (
        "Poruke sa kontakt forme stižu na email prodavnice. Koristimo vaš email za odgovor. "
        "Ne šaljite osetljive zdravstvene ili finansijske podatke bez potrebe. "
        "Zaštita od spama (honeypot) može se koristiti bez profilisanja."
    ),
    "7. Cookies and similar technologies": "7. Kolačići i slične tehnologije",
    "Our storefront uses cookies and similar storage that are necessary for the site to function, including:": (
        "Prodavnica koristi kolačiće neophodne za rad sajta, uključujući:"
    ),
    "Session cookie — keeps you logged in and maintains your shopping cart.": (
        "Sesijski kolačić — održava prijavu i korpu."
    ),
    "CSRF cookie — protects forms against cross-site request forgery.": (
        "CSRF kolačić — štiti forme od zloupotrebe."
    ),
    "Language cookie — remembers your Serbian or English language choice.": (
        "Jezički kolačić — pamti izbor srpskog ili engleskog jezika."
    ),
    "We do not currently use third-party marketing or analytics cookies on the public shop. If this changes, we will update this Policy and, where required, ask for consent before non-essential cookies are set.": (
        "Trenutno ne koristimo marketinške ili analitičke kolačiće trećih strana na javnoj prodavnici. "
        "Ako se to promeni, ažuriraćemo Politiku i, gde je potrebno, tražiti saglasnost."
    ),
    "8. Analytics": "8. Analitika",
    "Sales statistics inside our admin panel are generated from order data in our database and are not shared with external analytics providers. The public website does not use Google Analytics or similar visitor tracking at this time.": (
        "Statistika u admin panelu generiše se iz podataka o narudžbinama u bazi i ne deli se sa spoljnim analitičkim servisima. "
        "Javni sajt trenutno ne koristi Google Analytics niti slično praćenje posetilaca."
    ),
    "9. Email communication": "9. Email komunikacija",
    "We send transactional emails related to your orders (confirmation to you; operational notices to our team). Email is sent via our configured mail provider (SMTP). You cannot opt out of essential order emails while a contract is active. Marketing emails, if introduced later, will be sent only with your consent and with an unsubscribe option.": (
        "Šaljemo transakcione emailove vezane za narudžbine (potvrda vama; operativna obaveštenja timu). "
        "Email se šalje preko podešenog SMTP provajdera. Ne možete isključiti neophodne emailove dok je ugovor aktivan. "
        "Marketinški emailovi, ako budu uvedeni, samo uz saglasnost i opciju odjave."
    ),
    "10. Google Maps": "10. Google Maps",
    "Our contact page and footer may embed a Google Maps iframe to show our location. Google may collect data according to its own privacy policy when you interact with the map. The embed is loaded lazily to reduce unnecessary data transfer until you scroll to it.": (
        "Kontakt stranica i podnožje mogu prikazati Google Maps iframe sa lokacijom. Google može prikupljati podatke prema svojoj politici kada koristite mapu. "
        "Učitavanje je odloženo (lazy) da se smanji prenos podataka dok ne skrolujete do mape."
    ),
    "11. Retention": "11. Čuvanje podataka",
    "We keep personal data only as long as needed for the purposes above or as required by law (e.g. accounting archives). Order and invoice data are typically retained for the statutory period applicable in Serbia. Contact form messages are deleted when no longer needed for handling your inquiry.": (
        "Podatke čuvamo koliko je potrebno za navedene svrhe ili koliko zakon zahteva (npr. knjigovodstvena arhiva). "
        "Podaci o narudžbinama se obično čuvaju propisani rok u Srbiji. Poruke sa kontakt forme brišemo kada više nisu potrebne."
    ),
    "12. Your rights": "12. Vaša prava",
    "Under applicable law you may request access, correction, deletion, restriction of processing, data portability (where applicable), and object to processing based on legitimate interest. You may withdraw consent at any time without affecting prior lawful processing. You may lodge a complaint with the Commissioner for Information of Public Importance and Personal Data Protection of the Republic of Serbia.": (
        "U skladu sa zakonom možete zatražiti pristup, ispravku, brisanje, ograničenje obrade, prenosivost (gde se primenjuje) "
        "i prigovor na obradu zasnovanu na legitimnom interesu. Saglasnost možete povući u bilo kom trenutku. "
        "Žalbu možete podneti Povereniku za informacije od javnog značaja i zaštitu podataka o ličnosti RS."
    ),
    "To exercise your rights, contact us at the email above. We will respond within the statutory deadline.": (
        "Za ostvarivanje prava kontaktirajte nas na gornji email. Odgovorićemo u zakonskom roku."
    ),
    "13. Security": "13. Bezbednost",
    "We apply appropriate technical and organisational measures (HTTPS in production, access controls, hashed passwords, limited staff access). No method of transmission over the Internet is 100%% secure; please use a strong password for your account.": (
        "Primenjujemo odgovarajuće tehničke i organizacione mere (HTTPS u produkciji, kontrola pristupa, heširane lozinke). "
        "Nijedan prenos preko interneta nije 100%% bezbedan; koristite jaku lozinku."
    ),
    "14. International transfers": "14. Međunarodni prenos",
    "Data is primarily processed in Serbia/EU hosting. If we use processors outside Serbia/EEA (e.g. email or map providers), we ensure appropriate safeguards such as standard contractual clauses or adequacy decisions where required.": (
        "Podaci se primarno obrađuju na hostingu u Srbiji/EU. Ako koristimo obrađivače van Srbije/EEA (email, mape), "
        "obezbeđujemo odgovarajuće mere zaštite gde je potrebno."
    ),
    "15. Children": "15. Deca",
    "Our shop is not directed at children under 15. We do not knowingly collect data from children.": (
        "Prodavnica nije namenjena deci mlađoj od 15 godina. Svesno ne prikupljamo podatke dece."
    ),
    "16. Changes": "16. Izmene",
    "We may update this Policy. The current version is always on this page. Significant changes will be communicated where appropriate.": (
        "Politiku možemo ažurirati. Aktuelna verzija je uvek na ovoj stranici. O značajnim izmenama obavestićemo gde je primereno."
    ),
    "These Terms of Service govern online sales through the ": "Ovi Uslovi korišćenja regulišu online prodaju putem ",
    "webshop. They are intended for consumers in the Republic of Serbia. This document is for information purposes and does not replace individual legal advice.": (
        " prodavnice. Namenjeni su potrošačima u Republici Srbiji. Dokument je informativnog karaktera i ne zamenjuje individualni pravni savet."
    ),
    "1. Seller (operator)": "1. Prodavac (operator)",
    "The seller operating this webshop is:": "Prodavac koji vodi ovu internet prodavnicu je:",
    "Registered address:": "Adresa sedišta:",
    "2. Scope and products": "2. Obim i proizvodi",
    "We sell mixed/general merchandise through this website. Product descriptions, photos, and prices shown on product pages form part of the offer. We reserve the right to correct obvious errors and to update the assortment.": (
        "Prodajemo mešovitu/raznovrsnu robu putem ovog sajta. Opisi, fotografije i cene na stranicama proizvoda čine deo ponude. "
        "Zadržavamo pravo ispravke očiglednih grešaka i ažuriranja asortimana."
    ),
    "3. Account and guest checkout": "3. Nalog i kupovina bez naloga",
    "You may place orders as a guest or after creating a customer account. You are responsible for keeping your login credentials confidential and for activity under your account. Account data is processed according to our Privacy Policy.": (
        "Možete poručiti kao gost ili nakon registracije. Odgovorni ste za čuvanje pristupnih podataka i aktivnosti na nalogu. "
        "Podaci naloga se obrađuju prema Politici privatnosti."
    ),
    "4. Ordering process": "4. Proces poručivanja",
    "By submitting an order you make a binding purchase offer. We confirm receipt by email. A sales contract is concluded when we accept the order (confirmation or dispatch). Before placing an order you must accept these Terms and our Privacy Policy.": (
        "Slanjem narudžbine dajete obavezujuću ponudu za kupovinu. Potvrdu prijema šaljemo emailom. Ugovor o prodaji nastaje kada prihvatimo narudžbinu. "
        "Pre poručivanja morate prihvatiti ove Uslove i Politiku privatnosti."
    ),
    "You must provide accurate contact and delivery details.": "Morate uneti tačne kontakt i podatke za dostavu.",
    "Prices are shown in Serbian dinars (RSD) unless stated otherwise.": "Cene su u dinarima (RSD) osim ako nije drugačije naznačeno.",
    "Delivery cost is calculated at checkout based on the selected city.": "Cena dostave se računa pri plaćanju prema izabranom gradu.",
    "5. Prices and payment": "5. Cene i plaćanje",
    "All prices include applicable VAT where required by law. Payment is made on delivery (cash on delivery) unless we explicitly offer another method. You pay the courier upon receipt of the goods in cash or by card if available.": (
        "Sve cene uključuju PDV gde zakon zahteva. Plaćanje je pouzećem osim ako eksplicitno ponudimo drugi način. "
        "Kuriru plaćate pri preuzimanju gotovinom ili karticom ako je dostupno."
    ),
    "6. Delivery": "6. Dostava",
    "We deliver within the Republic of Serbia to the address you provide. Estimated delivery times are indicative and may depend on the carrier and your location. Risk of accidental loss or damage passes to you when you take physical possession of the goods.": (
        "Dostavljamo na teritoriji Republike Srbije na adresu koju navedete. Rokovi su orientacioni i zavise od kurira i lokacije. "
        "Rizik slučajnog gubitka prelazi na vas pri preuzimanju robe."
    ),
    "7. Right of withdrawal (consumers)": "7. Pravo na odustanak (potrošači)",
    "If you are a consumer under Serbian consumer protection law, you may withdraw from a distance contract within 14 days of receiving the goods, without giving a reason, subject to legal exceptions (e.g. sealed goods that cannot be returned for hygiene reasons, custom-made items, perishable goods). To exercise withdrawal, notify us clearly at our contact email before the deadline expires.": (
        "Ako ste potrošač po zakonu o zaštiti potrošača, možete odustati od ugovora na daljinu u roku od 14 dana od prijema robe, bez navođenja razloga, "
        "osim izuzetaka propisanim zakonom (npr. zapečaćena roba, proizvodi po meri, kvarljiva roba). Obaveštenje pošaljite na kontakt email pre isteka roka."
    ),
    "You must return the goods without undue delay and in any event within 14 days of sending your withdrawal notice. You bear direct return costs unless we agree otherwise or the law requires us to bear them. We will refund payments using the same means of payment, after we receive the goods or proof of return, in accordance with applicable law.": (
        "Robu vratite bez odlaganja, najkasnije u roku od 14 dana od obaveštenja o odustanku. Troškove povratne dostave snosite vi, osim ako drugačije ne ugovorimo ili zakon ne nalaže drugačije. "
        "Uplatu vraćamo istim sredstvom plaćanja nakon prijema robe ili dokaza o povratu, u skladu sa zakonom."
    ),
    "8. Complaints and conformity of goods": "8. Reklamacije i usaglašenost robe",
    "If goods are non-conforming or defective, you may submit a complaint within the statutory period. Contact us with your order number and a description of the issue. We will respond in line with the Law on Consumer Protection and related regulations.": (
        "Ako roba nije usaglašena ili je neispravna, možete podneti reklamaciju u zakonskom roku. Kontaktirajte nas sa brojem narudžbine i opisom problema. "
        "Postupićemo u skladu sa Zakonom o zaštiti potrošača i propisima."
    ),
    "9. Limitation of liability": "9. Ograničenje odgovornosti",
    "We are liable for damage caused intentionally or through gross negligence. For consumers, mandatory statutory rights are not limited. For business buyers, liability is limited to the maximum extent permitted by law. We are not responsible for indirect loss or delays caused by force majeure or third-party carriers beyond our reasonable control.": (
        "Odgovorni smo za štetu prouzrokovanu namerno ili krajnjom nepažnjom. Za potrošače se ne ograničavaju obavezna zakonska prava. "
        "Za pravna lica odgovornost je ograničena u meri dozvoljenoj zakonom. Nismo odgovorni za neizravnu štetu ili kašnjenja usled više sile ili kurira van naše razumne kontrole."
    ),
    "10. Intellectual property": "10. Intelektualna svojina",
    "Website content (text, images, logos, software) is protected by copyright and other rights. You may not copy or use it without our prior written consent except for personal browsing and ordering.": (
        "Sadržaj sajta (tekst, slike, logotipi, softver) je zaštićen autorskim i drugim pravima. Ne smete ga kopirati bez naše pisane saglasnosti, osim za lično pregledanje i poručivanje."
    ),
    "11. Personal data": "11. Lični podaci",
    "Processing of personal data is described in our": "Obrada ličnih podataka opisana je u našoj",
    "12. Dispute resolution": "12. Rešavanje sporova",
    "We aim to resolve complaints amicably. Consumers may also contact the competent market inspection authority or use out-of-court dispute resolution bodies where available under Serbian law. The courts of the Republic of Serbia have jurisdiction unless mandatory consumer rules provide otherwise.": (
        "Težimo da reklamacije rešimo mirno. Potrošači mogu kontaktirati nadležnu inspekciju tržišta ili koristiti vansudsko rešavanje sporova gde je dostupno. "
        "Za sudove je nadležna Republika Srbija, osim ako obavezna pravila o potrošačima ne predviđaju drugačije."
    ),
    "13. Changes": "13. Izmene",
    "We may update these Terms. The version published on this page applies to orders placed after publication. Material changes will be highlighted on the website where appropriate.": (
        "Uslove možemo ažurirati. Verzija objavljena na ovoj stranici važi za narudžbine posle objavljivanja. "
        "Bitne izmene ćemo istaknuti na sajtu gde je primereno."
    ),
    "This Privacy Policy explains how we collect and use personal data when you use the": (
        "Ova Politika privatnosti objašnjava kako prikupljamo i koristimo lične podatke kada koristite"
    ),
    "webshop. We process data in accordance with the Law on Personal Data Protection of the Republic of Serbia and, where applicable, the EU General Data Protection Regulation (GDPR).": (
        " prodavnicu. Podatke obrađujemo u skladu sa Zakonom o zaštiti podataka o ličnosti Republike Srbije i, gde je primenjivo, GDPR-om."
    ),
    "Email:": "Email:",
    "Phone:": "Telefon:",
    "Address:": "Adresa:",
    "Contact:": "Kontakt:",
    # Cookie banner
    "Cookies on this website": "Kolačići na ovom sajtu",
    "We use essential cookies so the shop works (cart, login, security). "
    "Google Maps on the contact page and footer is provided by Google and may involve "
    "their cookies — see our Privacy Policy.": (
        "Koristimo neophodne kolačiće da prodavnica radi (korpa, prijava, bezbednost). "
        "Google Maps na kontakt stranici i u podnožju obezbeđuje Google i može uključivati "
        "njihove kolačiće — pogledajte Politiku privatnosti."
    ),
    "Accept": "Prihvati",
    "Decline": "Odbij",
    "Cookie settings": "Podešavanja kolačića",
    "We do not use third-party marketing or analytics cookies on the public shop. "
    "The cookie notice informs you about essential cookies we use. Google Maps is "
    "embedded on the contact page and in the footer to show our location; when the "
    "map loads, Google may process data (including cookies) under its own privacy "
    "policy — see section 10.": (
        "Ne koristimo marketinške ili analitičke kolačiće trećih strana na javnoj prodavnici. "
        "Obaveštenje o kolačićima vas informiše o neophodnim kolačićima koje koristimo. "
        "Google Maps je ugrađen na kontakt stranici i u podnožju da prikaže našu lokaciju; "
        "kada se mapa učita, Google može obrađivati podatke (uključujući kolačiće) prema "
        "svojoj politici privatnosti — pogledajte tačku 10."
    ),
    "Our contact page and footer display an embedded Google Maps map of our store location. "
    "The map is loaded from Google’s servers when you open those pages. Google may collect "
    "and process personal data (such as IP address and interaction with the map) according "
    "to Google’s Privacy Policy and Terms of Service. We use the map to help you find us; "
    "we do not control Google’s processing. For questions about our use of the embed, "
    "contact us using the details in section 1.": (
        "Kontakt stranica i podnožje prikazuju ugrađenu Google Maps mapu naše lokacije. "
        "Mapa se učitava sa Google servera kada otvorite te stranice. Google može prikupljati "
        "i obrađivati lične podatke (npr. IP adresu i interakciju sa mapom) prema Google "
        "Politici privatnosti i Uslovima korišćenja. Mapu koristimo da vam pomognemo da nas "
        "pronađete; ne kontrolišemo Google obradu. Za pitanja o ugrađenoj mapi kontaktirajte "
        "nas putem podataka iz tačke 1."
    ),
    "This policy is provided for transparency. We recommend that a qualified "
    "legal adviser review it for your specific business circumstances.": (
        "Ova politika je data radi transparentnosti. Preporučujemo da je kvalifikovani "
        "pravni savetnik pregleda u skladu sa vašim poslovnim okolnostima."
    ),
}

PLURAL_TRANSLATIONS: dict[str, list[str]] = {
    "%(counter)s result": [
        "%(counter)s rezultat",
        "%(counter)s rezultata",
        "%(counter)s rezultata",
    ],
    "%(count)s item in your cart": [
        "%(count)s proizvod u korpi",
        "%(count)s proizvoda u korpi",
        "%(count)s proizvoda u korpi",
    ],
}


def main() -> int:
    po = polib.pofile(str(PO_PATH))
    filled = 0
    for entry in po:
        if entry.obsolete:
            continue
        key = entry.msgid
        if not key:
            continue
        if entry.msgid_plural:
            if key in PLURAL_TRANSLATIONS:
                entry.msgstr_plural = {i: PLURAL_TRANSLATIONS[key][i] for i in range(3)}
                if "fuzzy" in entry.flags:
                    entry.flags.remove("fuzzy")
                filled += 1
            continue
        if key in TRANSLATIONS:
            entry.msgstr = TRANSLATIONS[key]
            if "fuzzy" in entry.flags:
                entry.flags.remove("fuzzy")
            filled += 1
        elif not entry.translated():
            print(f"MISSING: {key[:100]!r}", file=sys.stderr)

    po.save(str(PO_PATH))
    print(f"Updated {filled} entries in {PO_PATH}")
    missing = [e for e in po if e.msgid and not e.obsolete and not e.translated()]
    print(f"Still untranslated: {len(missing)}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
