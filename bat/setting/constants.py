"""contacts for settings module."""

BUYER = "Buyer"
SELLER = "Seller"
DELIVERY_WHO_PAYS = ((BUYER, "Buyer"), (SELLER, "Seller"))


Air = "Air"
Sea = "Sea"
Road = "Road"
Railway = "Railway"
SHIP_TYPE = ((Air, "Air"), (Sea, "Sea"), (Road, "Road"), (Railway, "Railway"))

KG = "Kg"
CBM = "CBM"
SHIPRATE_TYPE = ((KG, "Kg"), (CBM, "CBM"))
