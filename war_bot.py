import requests
import time
import json
import os
import asyncio
import threading
from datetime import datetime, timedelta

# IP adresini öğren ve yazdır
try:
    ip = requests.get('https://httpbin.org/ip', timeout=5).json()['origin']
    print(f"🌐 Savaş Bot IP adresi: {ip}")
except:
    print("IP bulunamadı")

# Bot ayarları
BOT_TOKEN = "8121195624:AAGihP43rtCofFo2voDxRcGjMWcXym1_exg"
ADMIN_USERS = ["8114999904"]
COC_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImJkYzliMTQ1LTZkY2QtNDU0Mi1hNmNmLTgwMzViNDJiZWFjNyIsImlhdCI6MTc1MjAyNzAxMiwic3ViIjoiZGV2ZWxvcGVyLzRiYTU2MTc5LWE5NDgtMTBkYy0yNmI1LThkZjc5NjcyYjRmNCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjEzLjYxLjU2LjE5NyJdLCJ0eXBlIjoiY2xpZW50In1dfQ.xkmTiuBnozS8NSK8F1D8ST939QxlKj5qZ7EkRI45ZhDqCS406RFr0Jzh4hTJkEB3oWgNBDZh7aVs0xFqxBRWvw"
CLAN_TAG = "#2RGC8UPYV"
COC_API_BASE = "https://api.clashofclans.com/v1"

# Rütbe sistemı
ROLE_HIERARCHY = {
    'member': 1,
    'admin': 2, 
    'coLeader': 3,
    'leader': 4
}

ROLE_NAMES = {
    'member': 'Üye',
    'admin': 'Başkan', 
    'coLeader': 'Yardımcı Lider',
    'leader': 'Lider'
}

class WarBot:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        self.offset = 0
        self.data_file = "war_bot_data.json"
        self.users = {}
        self.today = datetime.now().strftime('%Y-%m-%d')
        print(f"⚔️ Savaş Bot başlatıldı - Tarih: {self.today}")
        
        # İlk savaş analizi
        self.analyze_current_war()
    
    def get_clan_data(self):
        """Clash of Clans API'den klan verilerini çek"""
        headers = {
            'Authorization': f'Bearer {COC_API_TOKEN}',
            'Accept': 'application/json'
        }
        
        try:
            clan_url = f"{COC_API_BASE}/clans/{CLAN_TAG.replace('#', '%23')}"
            response = requests.get(clan_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                clan_data = response.json()
                print(f"✅ Klan verisi alındı: {clan_data['name']}")
                return clan_data
            else:
                print(f"❌ COC API Hatası: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ COC API Bağlantı hatası: {e}")
            return None
    
    def get_clan_war_data(self):
        """Klan savaşı verilerini çek"""
        headers = {
            'Authorization': f'Bearer {COC_API_TOKEN}',
            'Accept': 'application/json'
        }
        
        try:
            war_url = f"{COC_API_BASE}/clans/{CLAN_TAG.replace('#', '%23')}/currentwar"
            response = requests.get(war_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                war_data = response.json()
                print(f"✅ Savaş verisi alındı")
                return war_data
            else:
                print(f"⚠️ Savaş verisi alınamadı: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Savaş API hatası: {e}")
            return None
    
    def analyze_war_matchup(self, our_clan, enemy_clan):
        """Savaş eşleştirmesi analizi - rakip klan güçlü mü?"""
        our_members = our_clan.get('members', [])
        enemy_members = enemy_clan.get('members', [])
        
        if not our_members or not enemy_members:
            return {'status': 'unknown', 'details': 'Üye bilgileri bulunamadı'}
        
        # Güç karşılaştırması
        our_total_th = sum(member.get('townhallLevel', 0) for member in our_members)
        enemy_total_th = sum(member.get('townhallLevel', 0) for member in enemy_members)
        
        our_avg_th = our_total_th / len(our_members)
        enemy_avg_th = enemy_total_th / len(enemy_members)
        
        # TH dağılımı analizi
        our_th_distribution = {}
        enemy_th_distribution = {}
        
        for member in our_members:
            th_level = member.get('townhallLevel', 0)
            our_th_distribution[th_level] = our_th_distribution.get(th_level, 0) + 1
        
        for member in enemy_members:
            th_level = member.get('townhallLevel', 0)
            enemy_th_distribution[th_level] = enemy_th_distribution.get(th_level, 0) + 1
        
        # Güç değerlendirmesi
        th_difference = enemy_avg_th - our_avg_th
        
        if th_difference > 0.5:
            strength_status = 'enemy_stronger'
            strength_emoji = '🔴'
            strength_text = 'Rakip daha güçlü'
        elif th_difference < -0.5:
            strength_status = 'we_stronger'
            strength_emoji = '🟢'
            strength_text = 'Bizim avantajımız var'
        else:
            strength_status = 'balanced'
            strength_emoji = '🟡'
            strength_text = 'Dengeli eşleşme'
        
        # En güçlü üyeler karşılaştırması
        our_top3 = sorted(our_members, key=lambda x: x.get('townhallLevel', 0), reverse=True)[:3]
        enemy_top3 = sorted(enemy_members, key=lambda x: x.get('townhallLevel', 0), reverse=True)[:3]
        
        return {
            'status': strength_status,
            'emoji': strength_emoji,
            'description': strength_text,
            'our_avg_th': round(our_avg_th, 1),
            'enemy_avg_th': round(enemy_avg_th, 1),
            'th_difference': round(th_difference, 1),
            'our_th_distribution': our_th_distribution,
            'enemy_th_distribution': enemy_th_distribution,
            'our_top3': [{'name': m.get('name'), 'th': m.get('townhallLevel')} for m in our_top3],
            'enemy_top3': [{'name': m.get('name'), 'th': m.get('townhallLevel')} for m in enemy_top3]
        }
    
    def suggest_targets_for_member(self, member, enemy_members, our_members):
        """Üye için hedef önerisi algoritması"""
        member_th = member.get('townhallLevel', 0)
        member_position = None
        
        # Üyenin pozisyonunu bul
        for i, our_member in enumerate(our_members, 1):
            if our_member.get('tag') == member.get('tag'):
                member_position = i
                break
        
        suggestions = []
        
        for i, enemy in enumerate(enemy_members, 1):
            enemy_th = enemy.get('townhallLevel', 0)
            enemy_attacks = enemy.get('attacks', [])
            
            # Hedef analizi
            th_difference = member_th - enemy_th
            
            # Skor hesaplama
            score = 50  # Base score
            
            # TH seviyesi bonus/malus
            if th_difference >= 0:
                score += min(th_difference * 20, 40)  # Aynı veya düşük TH bonus
            else:
                score -= abs(th_difference) * 15  # Yüksek TH cezası
            
            # Pozisyon uygunluğu
            position_diff = abs(member_position - i)
            if position_diff <= 2:
                score += 20  # Kendi seviyesi civarı bonus
            elif position_diff <= 5:
                score += 10
            
            # Zaten saldırılmış mı kontrolü
            attacked_by_us = False
            for our_member in our_members:
                for attack in our_member.get('attacks', []):
                    if attack.get('defenderTag') == enemy.get('tag'):
                        attacked_by_us = True
                        break
            
            if attacked_by_us:
                score -= 30  # Zaten saldırılmış ceza
            
            # Düşman saldırı sayısı (savunmasız hedefler tercih)
            if len(enemy_attacks) == 0:
                score += 15  # Henüz saldırmamış bonus
            
            # Öncelik belirleme
            if score >= 80:
                priority = 'high'
                priority_emoji = '🎯'
            elif score >= 60:
                priority = 'medium'
                priority_emoji = '⚡'
            elif score >= 40:
                priority = 'low'
                priority_emoji = '💫'
            else:
                priority = 'avoid'
                priority_emoji = '❌'
            
            suggestions.append({
                'position': i,
                'name': enemy.get('name'),
                'th_level': enemy_th,
                'score': round(score),
                'priority': priority,
                'emoji': priority_emoji,
                'th_difference': th_difference,
                'already_attacked': attacked_by_us,
                'reason': self.get_target_reason(th_difference, position_diff, attacked_by_us, score)
            })
        
        # En iyi 3 hedefi döndür
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:3]
    
    def get_target_reason(self, th_diff, pos_diff, attacked, score):
        """Hedef önerisi sebebi"""
        if attacked:
            return "Zaten saldırılmış"
        elif th_diff >= 1:
            return "Kolay hedef"
        elif th_diff == 0:
            return "Eşit seviye"
        elif th_diff == -1:
            return "Zorlayıcı ama yapılabilir"
        elif pos_diff <= 2:
            return "Pozisyon uygun"
        elif score >= 70:
            return "Güvenli seçim"
        else:
            return "Risk'li hedef"
    
    def generate_war_strategy(self, war_analysis):
        """Savaş stratejisi önerisi"""
        matchup = war_analysis['matchup_analysis']
        our_clan = war_analysis['our_clan']
        enemy_clan = war_analysis['enemy_clan']
        
        strategy = {
            'main_approach': '',
            'priority_actions': [],
            'warnings': [],
            'timeline': []
        }
        
        # Ana strateji belirleme
        if matchup['status'] == 'enemy_stronger':
            strategy['main_approach'] = 'defensive'
            strategy['priority_actions'] = [
                '🛡️ Savunmaya odaklan - güvenli hedefleri seç',
                '⭐ 2 yıldız stratejisi uygula',
                '🎯 Alt sıralarda güvenli puanları topla',
                '⚡ En güçlü üyeler üst sıraları temizlesin'
            ]
        elif matchup['status'] == 'we_stronger':
            strategy['main_approach'] = 'aggressive'
            strategy['priority_actions'] = [
                '🚀 Saldırgan git - 3 yıldız hedefle',
                '👑 Üst sıralar maksimum yıldız alsın',
                '🔥 Hızlı temizlik stratejisi',
                '💯 %100 hakim olma hedefi'
            ]
        else:
            strategy['main_approach'] = 'balanced'
            strategy['priority_actions'] = [
                '⚖️ Dengeli strateji - güvenli puanlar önce',
                '🎯 Kendi seviyende saldır',
                '⭐ 2 yıldız garantile, 3 yıldız dene',
                '🔄 Esnek takım çalışması'
            ]
        
        # Uyarılar
        remaining_attacks = our_clan['attacks_remaining']
        if remaining_attacks <= 5:
            strategy['warnings'].append('⚠️ Az saldırı hakkı kaldı - dikkatli ol!')
        
        if our_clan['stars'] < enemy_clan['stars']:
            strategy['warnings'].append('🔴 Gerideyiz - agresif strateji gerekli!')
        
        return strategy
    
    def get_war_analysis(self):
        """Detaylı savaş analizi ve eşleştirme değerlendirmesi"""
        war_data = self.get_clan_war_data()
        
        if not war_data or war_data.get('state') == 'notInWar':
            return None
        
        our_clan = war_data.get('clan', {})
        enemy_clan = war_data.get('opponent', {})
        
        analysis = {
            'war_state': war_data.get('state'),
            'preparation_start': war_data.get('preparationStartTime'),
            'start_time': war_data.get('startTime'),
            'end_time': war_data.get('endTime'),
            'team_size': war_data.get('teamSize'),
            'our_clan': {
                'name': our_clan.get('name'),
                'tag': our_clan.get('tag'),
                'level': our_clan.get('clanLevel'),
                'stars': our_clan.get('stars', 0),
                'destruction': our_clan.get('destructionPercentage', 0),
                'attacks_used': our_clan.get('attacksUsed', 0),
                'attacks_remaining': (war_data.get('teamSize', 0) * 2) - our_clan.get('attacksUsed', 0)
            },
            'enemy_clan': {
                'name': enemy_clan.get('name'),
                'tag': enemy_clan.get('tag'),
                'level': enemy_clan.get('clanLevel'),
                'stars': enemy_clan.get('stars', 0),
                'destruction': enemy_clan.get('destructionPercentage', 0),
                'attacks_used': enemy_clan.get('attacksUsed', 0)
            },
            'matchup_analysis': self.analyze_war_matchup(our_clan, enemy_clan),
            'member_status': self.analyze_war_members(our_clan, enemy_clan),
            'recommended_strategy': None
        }
        
        # Strateji önerisi
        analysis['recommended_strategy'] = self.generate_war_strategy(analysis)
        
        return analysis
    
    def analyze_war_members(self, our_clan, enemy_clan):
        """Savaş üye durumu ve atama analizi"""
        our_members = our_clan.get('members', [])
        enemy_members = enemy_clan.get('members', [])
        
        member_analysis = []
        
        for i, member in enumerate(our_members, 1):
            attacks = member.get('attacks', [])
            best_attack = member.get('bestOpponentAttack')
            
            # Saldırı durumu
            attack_status = 'not_attacked'
            total_stars = 0
            total_destruction = 0
            
            if attacks:
                attack_status = 'attacked'
                total_stars = sum(attack.get('stars', 0) for attack in attacks)
                total_destruction = sum(attack.get('destructionPercentage', 0) for attack in attacks)
            
            # Savunma durumu
            defense_status = 'not_defended'
            defended_stars = 0
            defended_destruction = 0
            
            if best_attack:
                defense_status = 'defended'
                defended_stars = best_attack.get('stars', 0)
                defended_destruction = best_attack.get('destructionPercentage', 0)
            
            # Hedef önerisi
            recommended_targets = self.suggest_targets_for_member(member, enemy_members, our_members)
            
            member_analysis.append({
                'position': i,
                'name': member.get('name'),
                'tag': member.get('tag'),
                'th_level': member.get('townhallLevel'),
                'attack_status': attack_status,
                'attacks_made': len(attacks),
                'total_stars': total_stars,
                'total_destruction': round(total_destruction, 1),
                'defense_status': defense_status,
                'defended_stars': defended_stars,
                'defended_destruction': round(defended_destruction, 1),
                'recommended_targets': recommended_targets,
                'priority': self.calculate_member_priority(member, attacks, best_attack)
            })
        
        return member_analysis
    
    def calculate_member_priority(self, member, attacks, best_defense):
        """Üye öncelik hesaplama"""
        priority_score = 0
        
        # Saldırı durumu
        if len(attacks) == 0:
            priority_score += 50  # Henüz saldırmamış - yüksek öncelik
        elif len(attacks) == 1:
            attack = attacks[0]
            if attack.get('stars', 0) < 2:
                priority_score += 30  # Kötü ilk saldırı - tekrar denemeli
            else:
                priority_score += 10  # İyi saldırı - ikinci saldırı için orta öncelik
        
        # TH seviyesi
        th_level = member.get('townhallLevel', 0)
        if th_level >= 12:
            priority_score += 20  # Yüksek TH - stratejik önemli
        
        # Savunma durumu
        if best_defense:
            defended_stars = best_defense.get('stars', 0)
            if defended_stars >= 2:
                priority_score -= 20  # İyi savunmuş - düşük öncelik
        
        return 'high' if priority_score >= 60 else 'medium' if priority_score >= 30 else 'low'
    
    def analyze_current_war(self):
        """Mevcut savaş durumunu analiz et"""
        print("🔍 Savaş analizi yapılıyor...")
        
        war_analysis = self.get_war_analysis()
        
        if war_analysis:
            print(f"⚔️ Savaş bulundu: {war_analysis['war_state']}")
            print(f"🆚 {war_analysis['our_clan']['name']} vs {war_analysis['enemy_clan']['name']}")
            print(f"📊 Skor: {war_analysis['our_clan']['stars']} - {war_analysis['enemy_clan']['stars']}")
        else:
            print("🏰 Şu anda savaşta değiliz")
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Mesaj gönder"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        if reply_markup:
            data['reply_markup'] = reply_markup
        
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Mesaj gönderme hatası: {e}")
            return None
    
    def get_updates(self):
        """Telegram güncellemelerini al"""
        url = f"{self.base_url}/getUpdates"
        params = {'offset': self.offset, 'timeout': 5}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Güncelleme alma hatası: {e}")
            return None
    
    def handle_start(self, message):
        """Start komutu"""
        user_id = str(message['from']['id'])
        first_name = message['from'].get('first_name', 'Komutan')
        chat_id = message['chat']['id']
        
        # Kullanıcıyı kaydet
        if user_id not in self.users:
            self.users[user_id] = {
                'name': first_name,
                'coc_tag': None,
                'join_date': self.today
            }
        
        # Savaş durumu özeti
        war_summary = self.get_war_summary()
        
        text = f"""⚔️ **Kemal'in Savaş Asistanı**

Hoş geldin {first_name}! 🎯

🤖 **Akıllı Savaş Özellikleri:**
• 🔍 Otomatik rakip analizi
• 🎯 Kişisel hedef önerileri
• 📊 Gerçek zamanlı savaş takibi
• 🏆 Performans değerlendirmesi

{war_summary}

⚔️ **Savaş Komutları:**
• **SAVAS** - Güncel savaş durumu
• **HEDEFIM** - Kişisel hedef önerileri
• **STRATEJI** - Savaş stratejisi
• **ANALIZ** - Detaylı rakip analizi
• **PERFORMANS** - Savaş performansı
• **YARDIM** - Tüm komutlar"""
        
        self.send_message(chat_id, text)
    
    def get_war_summary(self):
        """Savaş özeti hazırla"""
        war_analysis = self.get_war_analysis()
        
        if not war_analysis:
            return "🏰 **Durum:** Şu anda savaşta değiliz"
        
        our_clan = war_analysis['our_clan']
        enemy_clan = war_analysis['enemy_clan']
        matchup = war_analysis['matchup_analysis']
        
        war_state = war_analysis['war_state']
        if war_state == 'preparation':
            status_emoji = '⏳'
            status_text = 'Hazırlık Aşaması'
        elif war_state == 'inWar':
            status_emoji = '⚔️'
            status_text = 'Savaş Devam Ediyor'
        else:
            status_emoji = '✅'
            status_text = 'Savaş Bitti'
        
        return f"""🏁 **Savaş Durumu:**
{status_emoji} {status_text}
🆚 {our_clan['name']} vs {enemy_clan['name']}
⭐ Skor: {our_clan['stars']} - {enemy_clan['stars']}
{matchup['emoji']} {matchup['description']}
🎯 Kalan saldırı: {our_clan['attacks_remaining']}"""
    
    def handle_savas_command(self, message):
        """SAVAS komutu - Güncel savaş durumu"""
        chat_id = message['chat']['id']
        
        war_analysis = self.get_war_analysis()
        
        if not war_analysis:
            text = "🏰 **Şu anda savaşta değiliz**\n\n⏳ Savaş arama veya hazırlık aşamasında olabilirsiniz."
            self.send_message(chat_id, text)
            return
        
        war_state = war_analysis['war_state']
        our_clan = war_analysis['our_clan']
        enemy_clan = war_analysis['enemy_clan']
        matchup = war_analysis['matchup_analysis']
        
        if war_state == 'preparation':
            status_emoji = '⏳'
            status_text = 'Hazırlık Aşaması'
        elif war_state == 'inWar':
            status_emoji = '⚔️'
            status_text = 'Savaş Devam Ediyor'
        else:
            status_emoji = '✅'
            status_text = 'Savaş Bitti'
        
        text = f"""⚔️ **SAVAS DURUMU**

{status_emoji} **{status_text}**
🆚 **{our_clan['name']}** vs **{enemy_clan['name']}**

🏰 **Klan Karşılaştırması:**
• Bizim takım: Seviye {our_clan['level']} | {war_analysis['team_size']} kişi
• Rakip takım: Seviye {enemy_clan['level']} | {war_analysis['team_size']} kişi

{matchup['emoji']} **Güç Analizi: {matchup['description']}**
• Bizim ortalama TH: {matchup['our_avg_th']}
• Rakip ortalama TH: {matchup['enemy_avg_th']}
• Fark: {matchup['th_difference']:+.1f}

⭐ **Skor Durumu:**
• Bizim yıldız: {our_clan['stars']}
• Rakip yıldız: {enemy_clan['stars']}
• Bizim hasar: %{our_clan['destruction']}
• Rakip hasar: %{enemy_clan['destruction']}

🎯 **Saldırı Durumu:**
• Kullanılan: {our_clan['attacks_used']}
• Kalan: {our_clan['attacks_remaining']}

**Hedef önerileri:** HEDEFIM komutunu kullanın"""
        
        self.send_message(chat_id, text)
    
    def handle_hedefim_command(self, message):
        """HEDEFIM komutu - Kişisel hedef önerileri"""
        chat_id = message['chat']['id']
        user_id = str(message['from']['id'])
        
        war_analysis = self.get_war_analysis()
        
        if not war_analysis:
            text = "❌ Şu anda savaşta değiliz."
            self.send_message(chat_id, text)
            return
        
        # Kullanıcının COC tag'ini sor
        user_data = self.users.get(user_id, {})
        user_coc_tag = user_data.get('coc_tag')
        
        if not user_coc_tag:
            text = """🏷️ **COC Tag'inizi kaydedin:**

COC tag'inizi şu formatta yazın:
`#ABC123XYZ`

Örnek: `#2RGC8UPYV`

Tag'inizi yazdıktan sonra HEDEFIM komutunu tekrar kullanın."""
            self.send_message(chat_id, text)
            return
        
        # Kullanıcının savaş durumunu bul
        user_war_status = None
        for member in war_analysis['member_status']:
            if member['tag'] == user_coc_tag:
                user_war_status = member
                break
        
        if not user_war_status:
            text = "❌ Bu savaşta yer almıyorsunuz veya tag'iniz yanlış."
            self.send_message(chat_id, text)
            return
        
        remaining_attacks = 2 - user_war_status['attacks_made']
        
        text = f"""🎯 **KİŞİSEL HEDEF ÖNERİLERİ**

👤 **{user_war_status['name']}** (#{user_war_status['position']})
🏰 **TH{user_war_status['th_level']}** | Kalan saldırı: **{remaining_attacks}**

📊 **Mevcut Performansın:**
⚔️ Saldırı: {user_war_status['attacks_made']}/2
⭐ Toplam yıldız: {user_war_status['total_stars']}
💥 Toplam hasar: %{user_war_status['total_destruction']}
🛡️ Savunma: {user_war_status['defended_stars']} yıldız verildi

🎯 **ÖNERİLEN HEDEFLER:**"""
        
        for i, target in enumerate(user_war_status['recommended_targets'], 1):
            text += f"\n\n**{i}. {target['emoji']} HEDEF:**"
            text += f"\n• #{target['position']} {target['name']} (TH{target['th_level']})"
            text += f"\n• TH Farkı: {target['th_difference']:+d}"
            text += f"\n• Önem: {target['priority'].title()}"
            text += f"\n• Sebep: {target['reason']}"
            if target['already_attacked']:
                text += f"\n• ⚠️ Zaten saldırılmış"
        
        # Strateji önerisi
        if remaining_attacks > 0:
            priority_target = user_war_status['recommended_targets'][0] if user_war_status['recommended_targets'] else None
            
            text += f"\n\n💡 **STRATEJİ ÖNERİSİ:**"
            
            if user_war_status['attacks_made'] == 0:
                text += f"\n🥇 **İLK SALDIRI:** Güvenli hedefle başla"
                if priority_target:
                    text += f"\n   → #{priority_target['position']} {priority_target['name']} ideal"
            elif user_war_status['attacks_made'] == 1:
                if user_war_status['total_stars'] >= 2:
                    text += f"\n🥈 **İKİNCİ SALDIRI:** Risk alabilirsin"
                    text += f"\n   → Daha yüksek hedef dene"
                else:
                    text += f"\n🔄 **İKİNCİ SALDIRI:** Güvenli git"
                    text += f"\n   → Yıldız garantile"
            
            text += f"\n\n⏰ **Mevcut Öncelik:** {user_war_status['priority'].title()}"
        else:
            text += f"\n\n✅ **Tüm saldırılarını tamamladın!**"
            if user_war_status['total_stars'] >= 4:
                text += f"\n🏆 Mükemmel performans!"
            elif user_war_status['total_stars'] >= 3:
                text += f"\n👍 İyi iş çıkardın!"
            else:
                text += f"\n💪 Bir sonrakinde daha iyi olacak!"
        
        self.send_message(chat_id, text)
    
    def handle_strateji_command(self, message):
        """STRATEJI komutu - Savaş stratejisi"""
        chat_id = message['chat']['id']
        
        war_analysis = self.get_war_analysis()
        
        if not war_analysis:
            text = "❌ Şu anda savaşta değiliz."
            self.send_message(chat_id, text)
            return
        
        strategy = war_analysis['recommended_strategy']
        matchup = war_analysis['matchup_analysis']
        
        text = f"""🎯 **SAVAS STRATEJİSİ**

{matchup['emoji']} **Durum:** {matchup['description']}
🛡️ **Ana Yaklaşım:** {strategy['main_approach'].title()}

📋 **Öncelikli Aksiyonlar:**"""
        
        for action in strategy['priority_actions']:
            text += f"\n• {action}"
        
        if strategy['warnings']:
            text += f"\n\n⚠️ **Uyarılar:**"
            for warning in strategy['warnings']:
                text += f"\n• {warning}"
        
        # Rakip analizi
        text += f"\n\n🔍 **Rakip Analizi:**"
        text += f"\n• Ortalama TH: {matchup['enemy_avg_th']}"
        text += f"\n• Güç farkı: {matchup['th_difference']:+.1f}"
        
        # En güçlü rakipler
        text += f"\n\n👑 **Rakip En Güçlü 3:**"
        for i, enemy in enumerate(matchup['enemy_top3'], 1):
            text += f"\n{i}. {enemy['name']} (TH{enemy['th']})"
        
        self.send_message(chat_id, text)
    
    def handle_analiz_command(self, message):
        """ANALIZ komutu - Detaylı rakip analizi"""
        chat_id = message['chat']['id']
        user_id = str(message['from']['id'])
        
        if user_id not in ADMIN_USERS:
            text = "❌ Bu komut sadece adminler için!"
            self.send_message(chat_id, text)
            return
        
        war_analysis = self.get_war_analysis()
        
        if not war_analysis:
            text = "❌ Şu anda savaşta değiliz."
            self.send_message(chat_id, text)
            return
        
        matchup = war_analysis['matchup_analysis']
        member_status = war_analysis['member_status']
        
        # Saldırı yapmayan üyeler
        not_attacked = [m for m in member_status if m['attacks_made'] == 0]
        partial_attacks = [m for m in member_status if m['attacks_made'] == 1]
        
        text = f"""📊 **DETAYLI RAKİP ANALİZİ**

🔍 **Güç Karşılaştırması:**
• Bizim ortalama: TH{matchup['our_avg_th']}
• Rakip ortalama: TH{matchup['enemy_avg_th']}
• Fark: {matchup['th_difference']:+.1f}

📈 **TH Dağılımı (Rakip):**"""
        
        for th_level, count in sorted(matchup['enemy_th_distribution'].items(), reverse=True):
            text += f"\n• TH{th_level}: {count} üye"
        
        text += f"\n\n⚔️ **Saldırı Durumu:**"
        text += f"\n• Hiç saldırmadı: {len(not_attacked)} üye"
        text += f"\n• 1 saldırı yaptı: {len(partial_attacks)} üye"
        
        if not_attacked:
            text += f"\n\n❌ **Saldırı Beklenenler:**"
            for member in not_attacked[:5]:
                text += f"\n• {member['name']} (#{member['position']}) - TH{member['th_level']}"
        
        text += f"\n\n💡 **Öneriler:**"
        if matchup['status'] == 'enemy_stronger':
            text += f"\n🛡️ Savunmaya odaklan"
            text += f"\n⭐ 2 yıldız stratejisi uygula"
        elif matchup['status'] == 'we_stronger':
            text += f"\n🚀 Saldırgan strateji"
            text += f"\n🏆 3 yıldız hedefle"
        else:
            text += f"\n⚖️ Dengeli yaklaşım"
            text += f"\n🎯 Güvenli puanları topla"
        
        self.send_message(chat_id, text)
    
    def handle_performans_command(self, message):
        """PERFORMANS komutu - Savaş performansı"""
        chat_id = message['chat']['id']
        
        war_analysis = self.get_war_analysis()
        
        if not war_analysis:
            text = "❌ Şu anda savaşta değiliz."
            self.send_message(chat_id, text)
            return
        
        member_status = war_analysis['member_status']
        our_clan = war_analysis['our_clan']
        
        # Performans sıralaması
        active_members = [m for m in member_status if m['attacks_made'] > 0]
        active_members.sort(key=lambda x: (x['total_stars'], x['total_destruction']), reverse=True)
        
        # İstatistikler
        total_attacks_made = sum(m['attacks_made'] for m in member_status)
        total_possible = len(member_status) * 2
        attack_rate = (total_attacks_made / total_possible * 100) if total_possible > 0 else 0
        
        text = f"""🏆 **SAVAS PERFORMANSI**

📊 **Genel İstatistikler:**
• Saldırı kullanımı: {total_attacks_made}/{total_possible} (%{attack_rate:.1f})
• Toplam yıldız: {our_clan['stars']}
• Ortalama hasar: %{our_clan['destruction']}

🌟 **En İyi Performanslar:**"""
        
        for i, member in enumerate(active_members[:5], 1):
            star_avg = member['total_stars'] / member['attacks_made'] if member['attacks_made'] > 0 else 0
            text += f"\n{i}. **{member['name']}** (#{member['position']})"
            text += f"\n   ⚔️ {member['total_stars']} ⭐ ({member['attacks_made']} saldırı)"
            text += f"\n   📊 {star_avg:.1f} ⭐/saldırı"
        
        # Saldırı yapmayan üyeler
        not_attacked = [m for m in member_status if m['attacks_made'] == 0]
        if not_attacked:
            text += f"\n\n⚠️ **Saldırı Yapmayanlar ({len(not_attacked)}):**"
            for member in not_attacked[:3]:
                text += f"\n• {member['name']} (#{member['position']})"
        
        # Genel değerlendirme
        text += f"\n\n💭 **Değerlendirme:**"
        if attack_rate >= 90:
            text += f"\n🌟 Mükemmel katılım!"
        elif attack_rate >= 75:
            text += f"\n👍 İyi katılım"
        elif attack_rate >= 50:
            text += f"\n⚠️ Orta katılım"
        else:
            text += f"\n🔴 Düşük katılım - teşvik gerekli"
        
        self.send_message(chat_id, text)
    
    def handle_yardim_command(self, message):
        """YARDIM komutu - Tüm komutlar"""
        chat_id = message['chat']['id']
        
        text = f"""📚 **SAVAS BOTU YARDIM**

⚔️ **Temel Komutlar:**
• **SAVAS** - Güncel savaş durumu ve skor
• **HEDEFIM** - Kişisel hedef önerileri
• **STRATEJI** - Savaş stratejisi ve yaklaşım
• **PERFORMANS** - Takım performans raporu

🔍 **Admin Komutları:**
• **ANALIZ** - Detaylı rakip analizi
• **RAPOR** - Tam savaş raporu

📋 **Nasıl Kullanılır:**

1️⃣ **COC Tag Kaydet:**
   Tag'inizi `#ABC123XYZ` formatında yazın

2️⃣ **Hedef Önerileri:**
   HEDEFIM komutu size en uygun 3 hedefi gösterir

3️⃣ **Strateji Al:**
   STRATEJI komutu rakip analizine göre plan verir

4️⃣ **Performans Takip:**
   PERFORMANS ile takım durumunu görün

🎯 **İpuçları:**
• Savaş başlamadan önce STRATEJİ komutunu kullanın
• Her saldırıdan önce HEDEFIM ile hedef kontrol edin
• Takım performansını PERFORMANS ile takip edin

🤖 **Otomatik Özellikler:**
• Akıllı hedef algoritması
• Gerçek zamanlı savaş takibi
• TH bazlı güç analizi
• Performans puanlaması"""
        
        self.send_message(chat_id, text)
    
    def handle_text_message(self, message):
        """Metin mesajlarını işle"""
        user_id = str(message['from']['id'])
        chat_id = message['chat']['id']
        text = message['text'].upper()
        
        if text == '/START' or text == 'START':
            self.handle_start(message)
        elif text == 'SAVAS':
            self.handle_savas_command(message)
        elif text == 'HEDEFIM':
            self.handle_hedefim_command(message)
        elif text == 'STRATEJI':
            self.handle_strateji_command(message)
        elif text == 'ANALIZ':
            self.handle_analiz_command(message)
        elif text == 'PERFORMANS':
            self.handle_performans_command(message)
        elif text == 'YARDIM' or text == 'HELP':
            self.handle_yardim_command(message)
        elif text.startswith('#') and len(text) >= 4:
            # COC tag kaydet
            if user_id in self.users:
                self.users[user_id]['coc_tag'] = text
                self.send_message(chat_id, f"✅ **COC tag kaydedildi!**\n🏷️ **Tag:** `{text}`\n\n🎯 Artık **HEDEFIM** komutunu kullanabilirsiniz!")
        else:
            # Bilinmeyen komut
            self.send_message(chat_id, """❓ **Bilinmeyen komut**

📚 **Kullanılabilir komutlar:**
• **SAVAS** - Savaş durumu
• **HEDEFIM** - Hedef önerileri
• **STRATEJI** - Savaş stratejisi
• **PERFORMANS** - Performans raporu
• **YARDIM** - Tüm komutlar

🏷️ COC tag kaydetmek için: `#ABC123XYZ`""")
    
    def run(self):
        """Botu çalıştır"""
        print("⚔️ Kemal'in Savaş Asistanı")
        print("🤖 Akıllı Savaş Planlama Sistemi")
        print("🔄 Gerçek zamanlı savaş takibi aktif")
        print("📱 Telegram komutu: /start")
        print("🛑 Durdurmak için Ctrl+C")
        print("-" * 60)
        
        try:
            while True:
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    for update in updates['result']:
                        self.offset = update['update_id'] + 1
                        
                        if 'message' in update and 'text' in update['message']:
                            print(f"📨 Mesaj: {update['message']['text']}")
                            self.handle_text_message(update['message'])
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n🛑 Savaş Bot durduruldu!")
        except Exception as e:
            print(f"❌ Ana hata: {e}")

if __name__ == '__main__':
    bot = WarBot()
    bot.run()
