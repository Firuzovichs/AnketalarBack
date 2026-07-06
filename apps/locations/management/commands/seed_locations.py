from django.core.management.base import BaseCommand
from apps.locations.models import Country, Region, District

UZ_DATA = {
    "Toshkent shahri": ["Bektemir", "Chilonzor", "Hamza", "Mirzo Ulug'bek", "Mirobod", "Sergeli", "Shayxontohur", "Olmosoy", "Uchtepa", "Yakkasaroy", "Yunusobod", "Yashnobod"],
    "Toshkent viloyati": ["Angren", "Bekobod", "Bo'ka", "Bo'stonliq", "Chinoz", "Chirchiq", "Ohangaron", "Olmaliq", "Parkent", "Piskent", "Qibray", "O'rtachirchiq", "Yuqorichirchiq", "Zangiota"],
    "Samarqand viloyati": ["Samarqand", "Ishtixon", "Jomboy", "Kattaqo'rg'on", "Narpay", "Nurobod", "Oqdaryo", "Payariq", "Pastdarg'om", "Paxtachi", "Qo'shrabot", "Toyloq", "Urgut"],
    "Buxoro viloyati": ["Buxoro", "G'ijduvon", "Jondor", "Kogon", "Qorakol", "Qorovulbozor", "Peshku", "Romitan", "Shofirkon", "Vobkent"],
    "Andijon viloyati": ["Andijon", "Asaka", "Baliqchi", "Bo'ston", "Buloqboshi", "Izboskan", "Jalaquduq", "Xo'jaobod", "Marhamat", "Oltinko'l", "Paxtaobod", "Qo'rg'ontepa", "Shahrixon", "Ulug'nor"],
    "Farg'ona viloyati": ["Farg'ona", "Bag'dod", "Beshariq", "Buvayda", "Dang'ara", "Furqat", "Hamza", "Oltiariq", "Qo'qon", "Quva", "Rishton", "So'x", "Toshloq", "Uchko'prik", "Yozyovon"],
    "Namangan viloyati": ["Namangan", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin", "Pop", "To'raqo'rg'on", "Uychi", "Yangiqo'rg'on"],
    "Qashqadaryo viloyati": ["Qarshi", "Chiroqchi", "Dehqonobod", "G'uzor", "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak", "Nishon", "Qamashi", "Shahrisabz", "Yakkabog'"],
    "Surxondaryo viloyati": ["Termiz", "Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on", "Muzrabot", "Oltinsoy", "Qumqo'rg'on", "Sariosiyo", "Sherobod", "Sho'rchi", "Uzun"],
    "Xorazm viloyati": ["Urganch", "Bog'ot", "Gurlan", "Xiva", "Xonqa", "Qo'shko'pir", "Shovot", "Tuproqqal'a", "Yangiariq", "Yangibozor"],
    "Navoiy viloyati": ["Navoiy", "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa", "Tomdi", "Uchquduq", "Xatirchi"],
    "Jizzax viloyati": ["Jizzax", "Arnasoy", "Baxmal", "Do'stlik", "Forish", "G'allaorol", "Mirzacho'l", "Paxtakor", "Sharof Rashidov", "Yangiobod", "Zomin", "Zarbdor"],
    "Sirdaryo viloyati": ["Guliston", "Baxt", "Boyovut", "Mirzaobod", "Oqoltin", "Sardoba", "Sayxunobod", "Shirin", "Xovos"],
    "Qoraqalpog'iston": ["Nukus", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a", "Kegeyli", "Mo'ynoq", "Qanliko'l", "Qo'ng'irot", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli"],
}


class Command(BaseCommand):
    help = "O'zbekiston viloyat va tumanlarini bazaga yuklash"

    def handle(self, *args, **kwargs):
        uz, _ = Country.objects.get_or_create(
            code='UZ', defaults={'name': 'Uzbekistan', 'name_uz': "O'zbekiston"}
        )
        total = 0
        for region_name, districts in UZ_DATA.items():
            region, _ = Region.objects.get_or_create(
                country=uz, name=region_name,
                defaults={'name_uz': region_name}
            )
            for d in districts:
                District.objects.get_or_create(
                    region=region, name=d,
                    defaults={'name_uz': d}
                )
                total += 1
        self.stdout.write(self.style.SUCCESS(
            f"✅ O'zbekiston: 1 davlat, {len(UZ_DATA)} viloyat, {total} tuman yuklandi."
        ))
