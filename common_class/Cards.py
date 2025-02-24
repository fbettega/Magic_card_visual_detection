import re

class Card:
    def __init__(self, data):
        self.id = data.get("id")
        self.layout = data.get("layout")
        self.set = data.get("set", "")
        self.set_name = data.get("set_name", "")
        self.set_type = data.get("set_type", "")
        self.collector_number = data.get("collector_number", "")
        self.digital = data.get("digital", False)
        self.border_color = data.get("border_color", "")
        self.frame = data.get("frame", "")
        self.artist = data.get("artist", "")
        self.flavor_text = data.get("flavor_text", "")

        # Vérification si la carte a plusieurs faces
        self.card_faces = data.get("card_faces", [])

        if self.card_faces:
            # Face avant
            self.name_front = self.card_faces[0].get("name", "Unknown Front")
            self.oracle_text_front = self.card_faces[0].get("oracle_text", "")
            self.mana_cost_front = self.card_faces[0].get("mana_cost", "")
            self.type_line_front = self.card_faces[0].get("type_line", "")
            self.power_front = self.card_faces[0].get("power", "")
            self.toughness_front = self.card_faces[0].get("toughness", "")
            self.colors_front = self.card_faces[0].get("colors", [])

            # Face arrière (si présente)
            if len(self.card_faces) > 1:
                self.name_back = self.card_faces[1].get("name", "Unknown Back")
                self.oracle_text_back = self.card_faces[1].get("oracle_text", "")
                self.mana_cost_back = self.card_faces[1].get("mana_cost", "")
                self.type_line_back = self.card_faces[1].get("type_line", "")
                self.power_back = self.card_faces[1].get("power", "")
                self.toughness_back = self.card_faces[1].get("toughness", "")
                self.colors_back = self.card_faces[1].get("colors", [])
            else:
                self.name_back = self.oracle_text_back = self.mana_cost_back = ""
                self.type_line_back = self.power_back = self.toughness_back = ""
                self.colors_back = []
        
        else:
            # Cartes normales (non double face)
            self.name = data.get("name", "Unknown")
            self.oracle_text = data.get("oracle_text", "")
            self.mana_cost = data.get("mana_cost", "")
            self.type_line = data.get("type_line", "")
            self.power = data.get("power", "")
            self.toughness = data.get("toughness", "")
            self.colors = data.get("colors", [])

        # Gestion des images
        self.image_uris = data.get("image_uris", {})
    def __repr__(self):
        if self.card_faces:
            return (f"Card({self.name_front} // {self.name_back}, {self.type_line_front} // {self.type_line_back}, "
                    f"Set: {self.set_name}, Collector #: {self.collector_number})")
        else:
            return (f"Card({self.name}, {self.type_line}, {self.rarity}, "
                    f"Set: {self.set_name}, Collector #: {self.collector_number})")

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
                    images.append((image_url, f"{self.id}_{face_name}.jpg"))

        elif self.image_uris:
            image_url = self.image_uris.get("normal")
            if image_url:
                name_cleaned = self.sanitize_filename(self.name)
                images.append((image_url, f"{self.id}_{name_cleaned}.jpg"))

        return images
