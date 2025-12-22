import requests
from datetime import date, timedelta, datetime
import json
from dotenv import load_dotenv
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import ast
import pycountry

# CLOUDBEDS
def ultima_sexta():
    hoje = date.today()
    dia_da_semana = hoje.weekday()

    dias_atras = (dia_da_semana - 4 + 7) % 7
    
    if dias_atras == 0:
        dias_atras = 7

    sexta = hoje - timedelta(days=dias_atras)
    return sexta

def hotel_name_change(name = "El Misti Hostel Ipanema"):
    global hotel 
    hotel = name

def get_check_outs():
    path = './_internal/0_jsons/'
    try:
        os.mkdir(path)
    except:
        pass

    path = './_internal/'

    api_key_name = {
        'El Misti Hostel Ipanema': "API_KEY_IPANEMA",

        'El Misti Suites Copacabana': "API_KEY_COPACABANA",

        'El Misti Coliving Obelisco': "API_KEY_OBELISCO",

        'El Misti Centro Buenos Aires': "API_KEY_CENTRO",

        'El Misti Maipu Buenos Aires': "API_KEY_MAIPU",
    }

    if os.path.exists(path + "api_key.env"):
        load_dotenv(path + "api_key.env")
        api_key = os.getenv(api_key_name[hotel])
    else:
        raise Exception("API_KEY não achada!")
    
    if api_key == "xxx":
        raise Exception("Hotel não possui API_KEY!")

    hoje = date.today()
    #semana_passada = hoje - timedelta(days=7)
    semana_passada = ultima_sexta()

    if hoje.day < 8:
        semana_passada = hoje - timedelta(hoje.day-1)

    url = "https://api.cloudbeds.com/api/v1.3/getReservations"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key
    }

    params = {
        "checkOutFrom": semana_passada,
        "status": "checked_out",
        "pageSize": 100,
    }

    response = requests.get(url, headers=headers, params=params)

    response_json = json.loads(response.text)
    total = response_json["total"]

    if total > 100:
        page_number = 1

        total_pages = total//100
        if total%100 > 0:
            total_pages += 1

        while page_number < total_pages:
            page_number += 1
            params["pageNumber"] = page_number

            response = requests.get(url, headers=headers, params=params)

            response_json["data"] += json.loads(response.text)["data"]
    
    del response_json["success"]
    del response_json["count"]

    response_json["data"]
    if 'total' in response_json.keys():
        total = response_json['total']
    else:
        total = 0

    response_json['Booking'] = 0
    response_json['Hostel World'] = 0
    response_json['Outros'] = total

    with open('./_internal/0_jsons/Checkouts - {} - {}.json'.format(hotel, hoje), 'w', encoding="utf-8") as f:
        json.dump(response_json, f, indent=4)

    read_reservations()

def read_reservations():
    hoje = date.today()

    if os.path.exists('./_internal/0_jsons/Checkouts - {} - {}.json'.format(hotel, hoje)) == False:
        get_check_outs()

    with open('./_internal/0_jsons/Checkouts - {} - {}.json'.format(hotel, hoje), 'r', encoding="utf-8") as f:
        reservations = json.load(f)

    sources = {'Booking.com': 0, 'Hostelworld': 0, 'Outros': 0}

    for reservation in reservations['data']:
        nome = reservation['sourceName']
        
        if 'Booking.com' in nome:
            nome = 'Booking.com'
        elif 'Hostelworld' in nome:
            nome = 'Hostelworld'

        if reservation['sourceName'] not in sources:
            sources[nome] = 1
        else:
            sources[nome] += 1

    total = reservations["total"]
    reservations["Booking"] = sources['Booking.com']
    reservations["Hostel World"] = sources['Hostelworld']
    reservations["Outros"] = total - sources['Booking.com'] - sources['Hostelworld']

    with open('./_internal/0_jsons/Checkouts - {} - {}.json'.format(hotel, hoje), 'w', encoding="utf-8") as f:
        json.dump(reservations, f, indent=4)

def get_hospedes():
    path = './_internal/0_jsons/'
    try:
        os.mkdir(path)
    except:
        pass

    path = './_internal/'

    api_key_name = {
        'El Misti Hostel Ipanema': "API_KEY_IPANEMA",

        'El Misti Suites Copacabana': "API_KEY_COPACABANA",

        'El Misti Coliving Obelisco': "API_KEY_OBELISCO",

        'El Misti Centro Buenos Aires': "API_KEY_CENTRO",

        'El Misti Maipu Buenos Aires': "API_KEY_MAIPU",
    }

    if os.path.exists(path + "api_key.env"):
        load_dotenv(path + "api_key.env")
        api_key = os.getenv(api_key_name[hotel])
    else:
        raise Exception("API_KEY não achada!")
    
    if api_key == "xxx":
        raise Exception("Hotel não possui API_KEY!")

    hoje = date.today()
    amn = hoje + timedelta(days=1)
    diaAlvo = hoje + timedelta(days=7)

    url = "https://api.cloudbeds.com/api/v1.3/getReservations"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key
    }

    params = {
        "checkInFrom": amn,
        "checkInTo": diaAlvo,
        "pageSize": 100,
        "includeGuestsDetails": True,
        "includeAllRooms": True,
    }

    response = requests.get(url, headers=headers, params=params)

    response_json = json.loads(response.text)
    ts = datetime.now().timestamp()
    print('{} - {}'.format(ts, response_json))
    total = response_json["total"]

    if total > 100:
        page_number = 1

        total_pages = total//100
        if total%100 > 0:
            total_pages += 1

        while page_number < total_pages:
            page_number += 1
            params["pageNumber"] = page_number

            response = requests.get(url, headers=headers, params=params)

            response_json["data"] += json.loads(response.text)["data"]
    
    del response_json["success"]
    del response_json["count"]

    with open('./_internal/0_jsons/Reservas - {} - {}.json'.format(hotel, hoje), 'w', encoding="utf-8") as f:
        json.dump(response_json, f, indent=4)

def ler_futuros_hospedes():
    hoje = date.today()

    if os.path.exists('./_internal/0_jsons/Reservas - {} - {}.json'.format(hotel, hoje)) == False:
        get_hospedes()

    with open('./_internal/0_jsons/Reservas - {} - {}.json'.format(hotel, hoje), 'r', encoding="utf-8") as f:
        hospedes = json.load(f)

    hospedes_final = []

    with open('./_internal/paises.json', "r", encoding="utf-8") as file:
        paises = file.read()
        paises = json.loads(paises)

    sources = {}
    for i, reservation in enumerate(hospedes['data']):
        if reservation["status"] == "canceled":
            continue
        status = ''
        if reservation["status"] == "not_confirmed":
            status = "Não Confirmado"
        elif reservation["status"] == "confirmed":
            status = "Confirmado"

        id = reservation['guestID']

        origem = reservation['sourceName']
        if origem[:7] == 'Central':
            origem = 'Central'
        elif 'Website' in origem:
            origem = 'site'
        elif 'Booking' in origem:
            origem = 'Booking'
        elif 'Hostelworld' in origem:
            origem = 'Hostelworld'
        elif origem[:8] == 'Recovery':
            origem = 'Recovery'

        inicio = datetime.strptime(reservation['startDate'], "%Y-%m-%d").date()
        final = datetime.strptime(reservation['endDate'], "%Y-%m-%d").date()

        room_name = ''
        for room in reservation['rooms']:
            room_name += ', ' + room['roomName']
        room_name = room_name[2:]

        telefone = reservation['guestList'][id]['guestPhone']
        if telefone == '' or telefone == '0':
            telefone = reservation['guestList'][id]['guestEmail']

        pais = reservation['guestList'][id]['guestCountry']
        if pais != '00' and pais != None:
            pais = pycountry.countries.get(alpha_2=pais).alpha_3
            try:
                pais = paises["countries." + pais]
            except:
                pais = pycountry.countries.get(alpha_2=pais).alpha_3
        else:
            pais = ''

        hospedes_final.append({
            'Status': status,
            'Número da Reserva': reservation['reservationID'],
            'Origem da Reserva': origem,
            'Telefone': telefone,
            'País': pais,
            'Nome': reservation['guestName'],
            'Data de Chegada': reservation['startDate'],
            'Data de Partida': reservation['endDate'],
            'Noites de Quarto': (final - inicio).days,
            'Hóspedes': int(reservation['adults']) + int(reservation['children']),
            'Tipo de Acomodação': reservation['rooms'][0]['roomTypeName'],
            'Quarto(s)': room_name,
        })

        if origem not in sources:
            sources[origem] = 1
        else:
            sources[origem] += 1

    hospedes_final = {"data": hospedes_final}
    with open('./_internal/0_jsons/Contatos - {} - {}.json'.format(hotel, hoje), 'w', encoding="utf-8") as f:
        json.dump(hospedes_final, f, indent=4)
    
# BOOKING

def conversor_data_booking(data):
    dict_mes = {
        'janeiro': '01',
        'fevereiro': '02',
        'março': '03',
        'abril': '04',
        'maio': '05',
        'junho': '06',
        'julho': '07',
        'agosto': '08',
        'setembro': '09',
        'outubro': '10',
        'novembro': '11',
        'dezembro': '12'
    }

    data = data.split(' de ')
    data[1] = dict_mes[data[1]]
    data = '/'.join(data)

    return data

def get_reviews_booking(content, semana_passada):
    site = BeautifulSoup(content, 'html.parser')

    reviews = site.find(attrs={'data-testid': "review-cards"})
    reviews = reviews.find_all(attrs={'data-testid': "review-card"})

    reviews_dict = []
    soma = 0

    for review in reviews:
        ultima_data = review.find(attrs={'data-testid': "review-date"})
        ultima_data = ultima_data.text.strip().replace('\xa0', '').replace('·', '')
        ultima_data = ultima_data.replace('Avaliação: ', '')
        ultima_data = conversor_data_booking(ultima_data)
        ultima_data = datetime.strptime(ultima_data, "%d/%m/%Y").date()

        if ultima_data < semana_passada:
            break

        reviews_dict.append({
            'Nome': review.find(class_="b08850ce41 f546354b44"),
            'Data': str(ultima_data),
            'Nota': review.find(class_="f63b14ab7a dff2e52086"),
            'Pais': review.find(class_="d838fb5f41 aea5eccb71"),
            'Comodo': review.find(attrs={'data-testid': "review-room-name"}),
            'Diarias': review.find(attrs={'data-testid': "review-num-nights"}),
            'Dia': review.find(attrs={'data-testid': "review-stay-date"}),
            'Tipo': review.find(attrs={'data-testid': "review-traveler-type"}),
            'Titulo': review.find(attrs={'data-testid': "review-title"}),
            'Positivo': review.find(attrs={'data-testid': "review-positive-text"}),
            'Negativo': review.find(attrs={'data-testid': "review-negative-text"}),
            'Resposta': review.find(attrs={'data-testid': "review-partner-reply"})
        })

        for i in reviews_dict[-1]:
            if i == 'Data':
                continue
            elif reviews_dict[-1][i] != None:
                reviews_dict[-1][i] = reviews_dict[-1][i].text.strip().replace('\xa0', '').replace('·', '')
            else:
                reviews_dict[-1][i] = None

        soma += float(reviews_dict[-1]['Nota'].replace(',', '.'))

    return soma, ultima_data, reviews_dict

def booking(page, semana_passada):
    page.select_option('#reviewListSorters', value='NEWEST_FIRST')

    page.wait_for_load_state('networkidle')

    ultima_data = date.today()
    soma_total = 0

    booking_dict ={"Reviews": []}

    while ultima_data >= semana_passada:
        content = page.content()
        soma, ultima_data, review_dict = get_reviews_booking(content, semana_passada)

        booking_dict['Reviews'] += review_dict

        soma_total += soma

        if ultima_data >= semana_passada:
            page.keyboard.press("Control+End")
            page.wait_for_timeout(300)
            prox_pag = page.get_by_role("button", name="Página seguinte")
            prox_pag.click()
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)

    qtd = len(booking_dict['Reviews'])
    if qtd > 0:
        media = "{:.2f}".format(soma_total/qtd)
    else:
        media = '0.0'

    booking_dict['Soma'] = soma_total
    booking_dict['Quantidade'] = qtd
    booking_dict['Media'] = media

    page.close()

    return booking_dict

# HOSTEL WORLD

def get_reviews_hostel_world(content):
    site = BeautifulSoup(content, 'html.parser')
    site = site.find(attrs={'class': "review-details-body"})
    
    reviews = site.find_all(attrs={'class': "review"})

    soma = 0

    reviews_dict = []
    for review in reviews:
        descricao = review.find(attrs={'class': "avatar-description"}).text
        descricao = descricao.split(', ')
        
        reviews_dict.append({
            'Nome': review.find(attrs={'class': "avatar-title"}),
            'Data': review.find(attrs={'class': "review-card-date"}),
            'Nota': review.find(attrs={'class': "score"}),
            'Pais': descricao[2].strip(),
            'Idade': descricao[1].strip(),
            'Genero': descricao[0].strip(),
            'Tipo': review.find(attrs={'class': "title-rank"}),
            'Texto': review.find(attrs={'class': "review-card-text"}),
            'Resposta': review.find(attrs={'class': "property-reply-content large"})
        })

        for i in reviews_dict[-1]:
            if isinstance(reviews_dict[-1][i], str):
                continue
            elif reviews_dict[-1][i] != None:
                reviews_dict[-1][i] = reviews_dict[-1][i].text.strip()
            else:
                reviews_dict[-1][i] = None

        soma += float(reviews_dict[-1]['Nota'])

    return soma, reviews_dict

def hostel_world(page, semana_passada):
    page.wait_for_selector('.review')

    button_1 = page.locator(".menu-container").nth(1)
    button_1.click()

    button_2 = button_1.locator('button.item-content[value="all"]')
    button_2.click()

    page.wait_for_selector('.review')

    content = page.content()

    hostel_world_dict = {}
    soma, hostel_world_dict['Reviews'] = get_reviews_hostel_world(content)

    qtd = len(hostel_world_dict['Reviews'])
    if qtd > 0:
        media = "{:.2f}".format(soma/qtd)
    else:
        media = '0.0'

    hostel_world_dict['Soma'] = soma
    hostel_world_dict['Quantidade'] = qtd
    hostel_world_dict['Media'] = media

    page.close()

    return hostel_world_dict

# GOOGLE

def compara_dicts(d1, d2):
    ignorar = 'Data'
    for k1, v1 in d1.items():
        if k1 != ignorar and (k1 not in d2 or d2[k1] != v1):
            return False
    for k2, v2 in d2.items():
        if k2 != ignorar and k2 not in d1:
            return False
    return True

def store_last_reviews(reviews_dict):
    hoje = date.today()
    with open('./_internal/0_jsons/Ultimas Reviews - ' + hotel + ' - ' + str(hoje) + '.txt', 'w', encoding="utf-8") as f:
        print(reviews_dict, file=f)

def read_review_google(reviews_dict, review, data):
    texto = review.find_all(attrs={'class': "K7oBsc"})
    if len(texto) > 1:
        texto = texto[-1]
    else:
        texto = texto[0]

    reviews_dict.append({
        'Nome': review.find(attrs={'class': "DHIhE QB2Jof"}),
        'Data': data,
        'Nota': review.find(attrs={'class': "GDWaad"}),
        'Tipo': review.find(attrs={'class': "ThUm5b"}),
        'Texto': texto,
        'Quartos Nota': None,
        'Servico Nota': None,
        'Localizacao Nota': None,
        'Destaques': None,
        'Resposta': review.find(attrs={'class': "n7uVJf"}),
    })

    notas = review.find(attrs={'class': "X4nL7d"})
    if notas != None:
        divs = notas.find_all('div')
        for i, div in enumerate(divs[1:]):
            nota = div.text
            if 'Destaques do hotel' in nota:
                nota = nota.replace('Destaques do hotel', '')
                reviews_dict[-1]['Destaques'] = nota
            elif 'Quartos' in nota:
                nota = nota.replace('Quartos', '')
                reviews_dict[-1]['Quartos Nota'] = nota
            elif 'Serviço' in nota:
                nota = nota.replace('Serviço', '')
                reviews_dict[-1]['Servico Nota'] = nota
            elif 'Localização' in nota:
                nota = nota.replace('Localização', '')
                reviews_dict[-1]['Localizacao Nota'] = nota
            elif 'Hotel highlights' in nota:
                nota = nota.replace('Hotel highlights', '')
                reviews_dict[-1]['Destaques'] = nota
            elif 'Rooms' in nota:
                nota = nota.replace('Rooms', '')
                reviews_dict[-1]['Quartos Nota'] = nota
            elif 'Service' in nota:
                nota = nota.replace('Service', '')
                reviews_dict[-1]['Servico Nota'] = nota
            elif 'Location' in nota:
                nota = nota.replace('Location', '')
                reviews_dict[-1]['Localizacao Nota'] = nota

    for i in reviews_dict[-1]:
        if isinstance(reviews_dict[-1][i], str):
            continue
        elif reviews_dict[-1][i] != None:
            reviews_dict[-1][i] = reviews_dict[-1][i].text.strip()
        else:
            reviews_dict[-1][i] = None

    reviews_dict[-1]['Nota'] = reviews_dict[-1]['Nota'].replace('/5', '')
    reviews_dict[-1]['Texto'] = reviews_dict[-1]['Texto'].replace('(Original)', ' (Original)')

    return reviews_dict, reviews_dict[-1]['Nota']

def get_reviews_google(content, semana_passada):
    site = BeautifulSoup(content, 'html.parser')
    site = site.find(attrs={'class': "NCKy7b"})

    reviews = site.find_all(attrs={'class': "Svr5cf bKhjM"})

    lastReviews = []
    if os.path.exists('./_internal/0_jsons/Ultimas Reviews - ' + hotel + ' - ' + str(semana_passada) + '.txt'):
        with open('./_internal/0_jsons/Ultimas Reviews - ' + hotel + ' - ' + str(semana_passada) + '.txt', 'r', encoding="utf-8") as f:
            lastReviews = f.read()

        lastReviews = ast.literal_eval(lastReviews)

    qtd = 0
    soma = 0
    reviews_dict = []
    ultima_encontrada = False

    for review in reviews:
        data = review.find(attrs={'class': "iUtr1 CQYfx"}).text

        if "semanas" in data or "meses" in data or "mês" in data:
            break

        lugar = review.find(attrs={'class': "YhR3n"}).text

        if 'Google' in lugar:
            reviews_dict, nota = read_review_google(reviews_dict, review, data)

            for r in lastReviews:
                if compara_dicts(reviews_dict[-1], r):
                    reviews_dict = reviews_dict[:-1]
                    ultima_encontrada = True

            if ultima_encontrada:
                break

            nota = float(nota.split('/')[0])
            soma += nota
            qtd += 1

    if qtd > 0:
        media = "{:.2f}".format(soma/qtd)
    else:
        media = '0.0'

    google_dict = {}

    google_dict['Reviews'] = reviews_dict
    google_dict['Soma'] = soma
    google_dict['Quantidade'] = qtd
    google_dict['Media'] = media

    store_last_reviews(reviews_dict[:3])

    return google_dict

def google(page, semana_passada):
    button1 = page.get_by_role("option").nth(0)
    button1.click()

    mostRecent = page.get_by_role("option", name="Mais recentes")
    mostRecent.click()

    page.wait_for_timeout(1000)

    uma_semana_atras = False

    #                       "text=2 weeks ago on"
    #while not page.locator("text=2 semanas atrás no").first.is_visible():
    while uma_semana_atras == False:
        content = page.content()
        site = BeautifulSoup(content, 'html.parser')

        site = site.find(attrs={'class': "NCKy7b"})

        ultimaReview = site.find_all(attrs={'class': "Svr5cf bKhjM"})[-1].find(attrs={'class': "iUtr1 CQYfx"}).text

        if "semanas" in ultimaReview or "meses" in ultimaReview or "mês" in ultimaReview:
            uma_semana_atras = True
            break

        page.keyboard.press("Control+End")
        page.mouse.wheel(0, -100)
        page.wait_for_timeout(100)

    readmore = page.locator('text=Ler Mais').all()
    for rm in readmore:
        rm.click()

    content = page.content()
    site = BeautifulSoup(content, 'html.parser')

    google_dict = get_reviews_google(content, semana_passada)

    page.close()

    return google_dict

# PLAYWRIGHT

def get_dia():
    hoje = date.today()
    #semana_passada = hoje - timedelta(days=7)
    semana_passada = ultima_sexta()
    return hoje, semana_passada

def get_urls(hoje, semana_passada):
    url_dict = {
        'El Misti Hostel Ipanema': {
            'Booking': 'https://www.booking.com/hotel/br/el-misti-hostel-ipanema.pt-br.html#tab-reviews',
            'Hostel World': 'https://www.brazilian.hostelworld.com/pwa/hosteldetails.php/El-Misti-Hostel-Ipanema/Rio-de-Janeiro/264798?from={}&to={}&guests=2&display=reviews'.format(hoje, semana_passada),
            'Google': 'https://www.google.com/travel/search?q=el%20misti%20hostel%20ipanema&ts=CAAaGhIYEhIKBwjpDxALGA0SBwjpDxALGA4yAggAKgcKBToDQlJM&qs=MihDaG9JN2VTSDg4cVN3SmFzQVJvTkwyY3ZNVEZqYm5rd1lqSnNPQkFC&ap=ugEHcmV2aWV3cw&ved=0CAAQ5JsGahcKEwjA4NK22N2QAxUAAAAAHQAAAAAQBA',
        },

        'El Misti Suites Copacabana': {
            'Booking': 'https://www.booking.com/hotel/br/apartamento-5-de-julho.pt-br.html#tab-reviews',
            'Hostel World': None,
            'Google': 'https://www.google.com/travel/search?q=El%20Misti%20Suites&g2lb=4965990%2C72317059%2C72414906%2C72471280%2C72485658%2C72560029%2C72573224%2C72601598%2C72647020%2C72686036%2C72803964%2C72882230%2C72958624%2C72959983%2C73059275%2C73064764%2C73107089%2C73125229%2C73157411%2C73198317&ts=CAAaGhIYEhIKBwjpDxALGBASBwjpDxALGBEyAggAKgcKBToDQlJM&qs=MihDaG9JeU5mX3NvaTF5b0RWQVJvTkwyY3ZNVEZuT0dKM2NYSTJNeEFC&ap=ugEHcmV2aWV3cw&ved=0CAAQ5JsGahcKEwjIyfC_sfWQAxUAAAAAHQAAAAAQBA',
        },

        'El Misti Coliving Obelisco': {
            'Booking': 'https://www.booking.com/hotel/ar/el-misti-coliving-obelisco.pt-br.html#tab-reviews',
            'Hostel World': None,
            'Google': 'https://www.google.com/travel/search?q=el%20misti%20coliving%20obelisco%20hostelworld&g2lb=4965990%2C72317059%2C72414906%2C72471280%2C72485658%2C72560029%2C72573224%2C72601598%2C72647020%2C72686036%2C72803964%2C72882230%2C72958624%2C72959983%2C73059275%2C73064764%2C73107089%2C73125229%2C73157411%2C73198317&hl=pt-BR&gl=br&cs=1&ssta=1&ts=CAEaRwopEicyJTB4OTViY2NiNGFkNmE1Yzg3NToweDNmODU0Nzc2OTExNDk3NGUSGhIUCgcI6Q8QCxgQEgcI6Q8QCxgRGAEyAggC&qs=CAEyE0Nnb0l6cTdTaU9udTBjSV9FQUU4AkIJCU6XFJF2R4U_QgkJTpcUkXZHhT8&ap=ugEHcmV2aWV3cw&ictx=111&ved=0CAAQ5JsGahcKEwiguKC1svWQAxUAAAAAHQAAAAAQBw',
        },

        'El Misti Centro Buenos Aires': {
            'Booking': 'https://www.booking.com/hotel/ar/el-misti-buenos-aires.pt-br.html#tab-reviews',
            #'Hostel World': 'https://www.brazilian.hostelworld.com/pwa/hosteldetails.php/El-Misti-Hotel-Buenos-Aires-Centro/Buenos-Aires/318636?from={}&to={}&guests=2&display=reviews'.format(hoje, semana_passada),
            'Hostel World': None,
            'Google': 'https://www.google.com/travel/search?q=el%20misti%20buenos%20aires&g2lb=4965990%2C72317059%2C72414906%2C72471280%2C72485658%2C72560029%2C72573224%2C72601598%2C72647020%2C72686036%2C72803964%2C72882230%2C72958624%2C72959983%2C73059275%2C73064764%2C73107089%2C73125229%2C73157411%2C73198317&hl=pt-BR&gl=br&cs=1&ssta=1&ts=CAESCgoCCAMKAggDEAAaHBIaEhQKBwjpDxALGBASBwjpDxALGBEYATICCAIqBwoFOgNCUkw&qs=CAEyFENnc0lxOHVGM3YyTnZPSFJBUkFCOAhCCRHndm_ckXH1BUIJEfGnfUNu3eAYQgkRRLTrddBYB0JaUTJPqgFMEAEqDCIIZWwgbWlzdGkoADIfEAEiG_C_dvvkEUrU3z5-NAR6xAG0_EntXyCQW61cwDIZEAIiFWVsIG1pc3RpIGJ1ZW5vcyBhaXJlcw&ap=aAG6AQdyZXZpZXdz&ictx=111',
        },

        'El Misti Maipu Buenos Aires': {
            'Booking': 'https://www.booking.com/hotel/ar/el-misti-suites-buenos-aires.pt-br.html#tab-reviews',
            'Hostel World': None,
            'Google': 'https://www.google.com/travel/search?q=el%20misti%20buenos%20aires&g2lb=4965990%2C72317059%2C72414906%2C72471280%2C72485658%2C72560029%2C72573224%2C72601598%2C72647020%2C72686036%2C72803964%2C72882230%2C72958624%2C72959983%2C73059275%2C73064764%2C73107089%2C73125229%2C73157411%2C73198317&hl=pt-BR&gl=br&cs=1&ssta=1&ts=CAESCgoCCAMKAggDEAAaHBIaEhQKBwjpDxALGBASBwjpDxALGBEYATICCAIqBwoFOgNCUkw&qs=CAEyE0Nnb0k5dm43a2FYVjNKSXhFQUU4CEIJEed2b9yRcfUFQgkR8ad9Q27d4BhCCRFEtOt10FgHQlpRMk-qAUwQASoMIghlbCBtaXN0aSgAMh8QASIb8L92--QRStTfPn40BHrEAbT8Se1fIJBbrVzAMhkQAiIVZWwgbWlzdGkgYnVlbm9zIGFpcmVz&ap=aAG6AQdyZXZpZXdz&ictx=111',
        },
    }

    return url_dict[hotel]

def playwright():
    path = './_internal/0_jsons/'
    try:
        os.mkdir(path)
    except:
        pass

    hoje, semana_passada = get_dia()
    url_dict = get_urls(hoje, semana_passada)
    reviews_dict = {}

    with sync_playwright() as p:
        print('Lançando browser...')
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--no-sandbox",
                "--no-zygote"
            ]
        )
        
        context = browser.new_context(locale='pt-BR')

        if url_dict['Booking'] != None:
            url = url_dict['Booking']

            page = context.new_page()

            print('\nAbrindo: ' + url + '\n')

            page.goto(url)

            dict = booking(page, semana_passada)
            reviews_dict['Booking'] = dict

        if url_dict['Hostel World'] != None:
            url = url_dict['Hostel World']

            page = context.new_page()

            print('\nAbrindo: ' + url + '\n')

            page.goto(url)

            dict = hostel_world(page, semana_passada)
            reviews_dict['Hostel World'] = dict

        else:
            reviews_dict['Hostel World'] = {"Reviews": [], "Soma": 0.0, "Quantidade": 0, "Media": "0.00"}

        if url_dict['Google'] != None:
            url = url_dict['Google']

            page = context.new_page()

            print('\nAbrindo: ' + url + '\n')

            page.goto(url)

            dict = google(page, semana_passada)
            reviews_dict['Google'] = dict

        browser.close()

        with open('./_internal/0_jsons/Reviews - {} - {}.json'.format(hotel, date.today()), 'w', encoding="utf-8") as f:
            json.dump(reviews_dict, f, indent=4)
