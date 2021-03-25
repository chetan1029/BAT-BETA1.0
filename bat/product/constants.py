CM = "cm"
IN = "in"
LENGTH_UNIT_TYPE = ((CM, "cm"), (IN, "in"))

PRODUCT_PARENT_STATUS = "Basic"
PRODUCT_STATUS_ACTIVE = "Active"
PRODUCT_STATUS_ARCHIVE = "Archive"
PRODUCT_STATUS_DRAFT = "Draft"
PRODUCT_STATUS_INACTIVE = "Inactive"
PRODUCT_STATUS_DISCONTINUED = "Discontinued"

PRODUCT_STATUS_CHOICE = [PRODUCT_STATUS_ACTIVE, PRODUCT_STATUS_ACTIVE.lower(),
                         PRODUCT_STATUS_ARCHIVE, PRODUCT_STATUS_ARCHIVE.lower(),
                         PRODUCT_STATUS_DRAFT, PRODUCT_STATUS_DRAFT.lower(),
                         PRODUCT_STATUS_DISCONTINUED, PRODUCT_STATUS_DISCONTINUED.lower()
                         ]
PRODUCT_STATUS_CHOICE2 = [PRODUCT_STATUS_ACTIVE, PRODUCT_STATUS_ACTIVE.lower(),
                          PRODUCT_STATUS_ARCHIVE, PRODUCT_STATUS_ARCHIVE.lower(),
                          PRODUCT_STATUS_DRAFT, PRODUCT_STATUS_DRAFT.lower(),
                          ]

PRODUCT_STATUS = {"active": PRODUCT_STATUS_ACTIVE,
                  "archive": PRODUCT_STATUS_ARCHIVE,
                  "draft": PRODUCT_STATUS_DRAFT,
                  "discontinued": PRODUCT_STATUS_DISCONTINUED}

AVAILABLE_IMPORT_FILE_EXTENSIONS = {"csv": ["csv"],
                                    "excel": ["xlsx"]
                                    }
