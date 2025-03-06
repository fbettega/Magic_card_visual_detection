import re

class Card:
    def __init__(self, data):
        self.id = data.get("id")
        self.layout = data.get("layout")
        self.set = data.get("set", "")
        self.set_name = data.get("set_name", "")
        self.rarity = data.get("rarity", "")
        self.set_type = data.get("set_type", "")
        self.collector_number = data.get("collector_number", "")
        self.digital = data.get("digital", False)
        self.border_color = data.get("border_color", "")
        self.frame = data.get("frame", "")
        self.artist = data.get("artist", "")
        self.flavor_text = data.get("flavor_text", "")
        self.language = data.get("lang", "")
        self.flavor_name = data.get("flavor_name", "")
        self.promo_types = data.get("promo_types", "")
        self.textless = data.get("textless", "")
        self.security_stamp = data.get("security_stamp", "")
        self.frame_effects = data.get("frame_effects", "")


        # Gestion des cartes en fonction de leur layout
        self.card_faces = data.get("card_faces", [])
        self.image_status = data.get("image_status", "")  # Ajout de image_status
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
        if self.layout in {"reversible_card","transform", "modal_dfc", "double_faced_token"}:
            # Cartes double face (recto/verso)
            self.name_front = self.card_faces[0].get("name", "Unknown Front")
            self.oracle_text_front = self.card_faces[0].get("oracle_text", "")
            self.mana_cost_front = self.card_faces[0].get("mana_cost", "")
            self.type_line_front = self.card_faces[0].get("type_line", "")
            self.power_front = self.card_faces[0].get("power", "")
            self.toughness_front = self.card_faces[0].get("toughness", "")
            self.loyalty_front = self.card_faces[0].get("loyalty", "")
            self.colors_front = self.card_faces[0].get("colors", [])
            self.image_uris_front = self.card_faces[0].get("image_uris", {})
            self.printed_text_front =  self.card_faces[0].get("printed_text", "")
            self.printed_name_front =  self.card_faces[0].get("printed_name", "")
            self.printed_type_line_front =  self.card_faces[0].get("printed_type_line", "")
            self.watermark_front =  self.card_faces[0].get("watermark", "")

            self.name_back = self.card_faces[1].get("name", "Unknown Back")
            self.oracle_text_back = self.card_faces[1].get("oracle_text", "")
            self.mana_cost_back = self.card_faces[1].get("mana_cost", "")
            self.type_line_back = self.card_faces[1].get("type_line", "")
            self.power_back = self.card_faces[1].get("power", "")
            self.toughness_back = self.card_faces[1].get("toughness", "")
            self.loyalty_back = self.card_faces[1].get("loyalty", "")
            self.colors_back = self.card_faces[1].get("colors", [])
            self.image_uris_back = self.card_faces[1].get("image_uris", {})
            self.printed_text_back =  self.card_faces[1].get("printed_text", "")
            self.printed_name_back =  self.card_faces[1].get("printed_name", "")
            self.printed_type_line_back =  self.card_faces[1].get("printed_type_line", "")
            self.watermark_back =  self.card_faces[1].get("watermark", "")
        elif self.layout in {"adventure", "split", "flip"}:
            # Cartes d'aventure ou fractionnées
            self.name_front = self.card_faces[0].get("name", "Unknown Front")
            self.oracle_text_front = self.card_faces[0].get("oracle_text", "")
            self.mana_cost_front = self.card_faces[0].get("mana_cost", "")
            self.type_line_front = self.card_faces[0].get("type_line", "")
            self.colors_front = self.card_faces[0].get("colors", [])
            self.image_uris_front = self.card_faces[0].get("image_uris", {})
            self.power_front = self.card_faces[0].get("power", "")
            self.toughness_front = self.card_faces[0].get("toughness", "")
            self.loyalty_front = self.card_faces[0].get("loyalty", "")

            self.printed_text_front =  self.card_faces[0].get("printed_text", "")
            self.printed_name_front =  self.card_faces[0].get("printed_name", "")
            self.printed_type_line_front =  self.card_faces[0].get("printed_type_line", "")
            self.watermark_front =  self.card_faces[0].get("watermark", "")

            if len(self.card_faces) > 1:
                self.name_back = self.card_faces[1].get("name", "Unknown Back")
                self.oracle_text_back = self.card_faces[1].get("oracle_text", "")
                self.mana_cost_back = self.card_faces[1].get("mana_cost", "")
                self.type_line_back = self.card_faces[1].get("type_line", "")
                self.colors_back = self.card_faces[1].get("colors", [])
                self.power_back = self.card_faces[1].get("power", "")
                self.toughness_back = self.card_faces[1].get("toughness", "")
                self.loyalty_back = self.card_faces[1].get("loyalty", "")

                self.printed_text_back =  self.card_faces[1].get("printed_text", "")
                self.printed_name_back =  self.card_faces[1].get("printed_name", "")
                self.printed_type_line_back =  self.card_faces[1].get("printed_type_line", "")
                self.watermark_back =  self.card_faces[1].get("watermark", "")
            else:
                self.name_back = self.oracle_text_back = ""
                self.mana_cost_back = self.type_line_back = ""
                self.colors_back = []
                self.type_line_back =  ""
                self.colors_back = ""
                self.power_back = ""
                self.toughness_back = ""
                self.loyalty_back = ""
                self.printed_text_back =   ""
                self.printed_name_back =   ""
                self.printed_type_line_back =   ""
                self.watermark_back =   ""

        else:
            # Cartes normales (simple face)
            self.name_front = data.get("name", "Unknown")
            self.oracle_text_front = data.get("oracle_text", "")
            self.mana_cost_front = data.get("mana_cost", "")
            self.type_line_front = data.get("type_line", "")
            self.power_front = data.get("power", "")
            self.toughness_front = data.get("toughness", "")
            self.loyalty_front = data.get.get("loyalty", "")
            self.colors_front = data.get("colors", [])
            self.image_uris_front = data.get("image_uris", {})
            # Textes imprimés
            self.printed_text_front = data.get("printed_text", "")
            self.printed_name_front = data.get("printed_name", "")
            self.printed_type_line_front = data.get("printed_type_line", "")
            self.watermark_front = data.get("watermark", "")

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

