import re

class Card:
    def __init__(self, data: dict):
        """
        Initialize a Card object from Scryfall bulk data.
        :param data: Dictionary containing card data from Scryfall.
        """
        # Basic card identifiers
        self.id: str = data.get("id", "")  # Unique identifier
        self.layout: str = data.get("layout", "")  # Card layout type
        self.set: str = data.get("set", "")  # Set code
        self.set_name: str = data.get("set_name", "")  # Full set name
        self.rarity: str = data.get("rarity", "")  # Rarity (common, uncommon, rare, mythic, etc.)
        self.set_type: str = data.get("set_type", "")  # Set type (core, expansion, etc.)
        self.collector_number: str = data.get("collector_number", "")  # Collector number
        self.digital: bool = data.get("digital", False)  # True if digital-only card
        self.border_color: str = data.get("border_color", "")  # Border color
        self.frame: str = data.get("frame", "")  # Frame version
        self.frame_effects: list = data.get("frame_effects", [])  # List of frame effects
        
        # Artist and flavor information
        self.artist: str = data.get("artist", "")  # Artist name
        self.flavor_text: str = data.get("flavor_text", "")  # Flavor text
        self.language: str = data.get("lang", "")  # Language code
        self.flavor_name: str = data.get("flavor_name", "")  # Flavor name (alternative name)
        
        # Promotional and security features
        self.promo: bool = data.get("promo", False)  # True if promotional card
        self.promo_types: list = data.get("promo_types", [])  # List of promo types
        self.textless: bool = data.get("textless", False)  # True if textless variant
        self.security_stamp: str = data.get("security_stamp", "")  # Security stamp identifier
        
        # Token status
        self.token: bool = self.layout in {'double_faced_token', 'token', 'emblem'} or self.set == 'token'
        
        # Card face data (for double-faced, split, and adventure cards)
        self.card_faces: list = data.get("card_faces", [])  # List of card face dictionaries
        self.image_status: str = data.get("image_status", "")  # Image status
                # Mapping des raretés vers la lettre correspondante
        rarity_mapping = {
            "common": "C",
            "uncommon": "U",
            "rare": "R",
            "mythic": "M",
            "bonus": "S",  # Pour les cartes 'bonus' ou 'special'
            "special": "S"
        }

        # Attribution de la lettre de rareté
        self.rarity_letter = rarity_mapping.get(self.rarity, "Unknown")

        # Handle multi-faced cards
        self.card_faces: list = data.get("card_faces", [])
        self.extract_card_faces(data)

    def extract_card_faces(self, data):
        """
        Extracts relevant card face details based on layout type.
        """
        if self.layout in {"reversible_card", "transform", "modal_dfc", "double_faced_token"}:
            # Double-faced cards (front/back)
            self.set_card_faces(data, double_sided=True)
        elif self.layout in {"adventure", "split", "flip"}:
            # Adventure, split, or flip cards
            self.set_card_faces(data, double_sided=False)
        else:
            # Single-faced cards
            self.set_single_face(data)

    def set_card_faces(self, data, double_sided: bool):
        """
        Sets attributes for cards with multiple faces.
        """
        self.name_front: str = self.card_faces[0].get("name", "Unknown Front")
        self.oracle_text_front: str = self.card_faces[0].get("oracle_text", "")
        self.mana_cost_front: str = self.card_faces[0].get("mana_cost", "")
        self.type_line_front: str = self.card_faces[0].get("type_line", "")
        self.colors_front: list = self.card_faces[0].get("colors", [])
        self.image_uris_front: dict = self.card_faces[0].get("image_uris", {})
        self.power_front: str = self.card_faces[0].get("power", "")
        self.toughness_front: str = self.card_faces[0].get("toughness", "")
        self.loyalty_front: str = self.card_faces[0].get("loyalty", "")
        
        if double_sided and len(self.card_faces) > 1:
            self.name_back: str = self.card_faces[1].get("name", "Unknown Back")
            self.oracle_text_back: str = self.card_faces[1].get("oracle_text", "")
            self.mana_cost_back: str = self.card_faces[1].get("mana_cost", "")
            self.type_line_back: str = self.card_faces[1].get("type_line", "")
            self.colors_back: list = self.card_faces[1].get("colors", [])
            self.power_back: str = self.card_faces[1].get("power", "")
            self.toughness_back: str = self.card_faces[1].get("toughness", "")
            self.loyalty_back: str = self.card_faces[1].get("loyalty", "")
        else:
            self.name_back = self.oracle_text_back = ""
            self.mana_cost_back = self.type_line_back = ""
            self.colors_back = []
            self.power_back = ""
            self.toughness_back = ""
            self.loyalty_back = ""

    def set_single_face(self, data):
        """
        Sets attributes for single-faced cards.
        """
        self.name_front: str = data.get("name", "Unknown")
        self.oracle_text_front: str = data.get("oracle_text", "")
        self.mana_cost_front: str = data.get("mana_cost", "")
        self.type_line_front: str = data.get("type_line", "")
        self.power_front: str = data.get("power", "")
        self.toughness_front: str = data.get("toughness", "")
        self.loyalty_front: str = data.get("loyalty", "")
        self.colors_front: list = data.get("colors", [])
        self.image_uris_front: dict = data.get("image_uris", {})

    def __repr__(self):
        attrs = vars(self)  # Récupère tous les attributs sous forme de dict
        attr_str = ", ".join(f"{k}={v!r}" for k, v in attrs.items())  # Formatte chaque clé-valeur
        return f"Card({attr_str})"


    def sanitize_filename(self, name):
        """Remplace les espaces et caractères spéciaux pour un nom de fichier valide."""
        return re.sub(r'[^\w.-]', '_', name)

    def get_images(self):
        """Récupère les URLs des images en tenant compte des cartes double face."""
        images = []
        if self.card_faces:
            for i, face in enumerate(self.card_faces):
                image_url = face.get("image_uris", {}).get("normal")
                if image_url:
                    face_name = self.sanitize_filename(face.get("name", f"face_{i}"))
                    face_type = "front" if i == 0 else "back"
                    images.append((image_url, f"{self.id}_{face_name}_{face_type}.jpg", self.image_status))

        elif self.image_uris_front:
            image_url = self.image_uris_front.get("normal")
            if image_url:
                name_cleaned = self.sanitize_filename(self.name_front)
                images.append((image_url, f"{self.id}_{name_cleaned}.jpg",self.image_status))
        return images

