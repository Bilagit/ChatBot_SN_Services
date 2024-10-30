import openai
import requests
import json
from bs4 import BeautifulSoup

# Clé de l'API OpenAI
openai.api_key = "your api key here"

# Initialisation des variables, propres à chaque session
class ResponseData:
    def __init__(self):
        self.first_time = True
        self.final_data = ""
        self.key_word = ""
    def to_json(self):
        return json.dumps(self.__dict__)
    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        response_data = ResponseData()
        response_data.__dict__.update(data)
        return response_data

# Fonction qui recupère les informations des demandes et retourne la réponse générée par ChatGPT
def search(user_question, response_data):
    if "True" in response_data.key_word:
            response_data.key_word = response_data.key_word.replace('True', '')
            response_data.key_word = response_data.key_word.replace('\n', '')
            url = f"https://senegalservices.sn/api/search?q={response_data.key_word}"
            try:
                main_request = requests.get(url, verify=False)
            except:
                    generated_response = "Oups ! Il semble qu'on a rencontré un problème veuillez réessayer, si le problème persiste veuillez recharger la page ou réessayer plus tard<br>"
                    return generated_response   
            if main_request.status_code == 200:
                json_data = json.loads(main_request.text)
                slugs = [hit["slug"] for hit in json_data["hits"] if "demarche_id" in hit]
                
                for word_to_search in slugs:
                    link = f"https://senegalservices.sn/api/demarche/{word_to_search}"
                    try:
                        request_2 = requests.get(link, verify=False)
                    except:
                        generated_response ="Oups ! Il semble qu'on a rencontré un problème veuillez réessayer, si le problème persiste veuillez recharger la page ou réessayer plus tard<br>"
                        return generated_response  
                    json_data2 = json.loads(request_2.text)
                    title = json_data2["titre"]
                    body = json_data2["corps"]
                    soup = BeautifulSoup(body, 'html.parser')
                    response_data.final_data += title + ' \n'
                    response_data.final_data += soup.get_text()
                    response_data.final_data += "Services administratifs à contacter\n"
                    for item in json_data2["service_administratifs"]:
                        slugs_services = item["slug"]
                        link_service = f"https://senegalservices.sn/api/services-administratifs/{slugs_services}"
                        request_3 = requests.get(link_service, verify=False)
                        json_data3 = json.loads(request_3.text)
                        name = json_data3["nom"]
                        mail = json_data3["email"]
                        adresse = json_data3["adresse"]
                        site_web = json_data3["site_web"]
                        response_data.final_data += f"nom : {name}"
                        response_data.final_data += f"mail : {mail}\n"
                        response_data.final_data += f"adresse : {adresse}\n"
                        response_data.final_data += f"site web : {site_web}\n"
                if not (len(response_data.final_data) == 0):
                    prompt = [{"role": "user", "content": f"""Contexte : Réponds à la demande de l'utilisateur dans le cadre des démarches administratives au Sénégal, en te basant sur les informations suivantes, si ça concerne plusieurs demandes liste les seulement sans donner de détails.
                    informations du site : {response_data.final_data}
                    Utilisateur : {user_question}
                    Réponse : 
                    """}]
                    try:
                        response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages = prompt,
                        max_tokens=800,
                        temperature=0.7
                        )
                    except openai.error.OpenAIError as e:
                        print("erreur openai : ", e.error)
                        generated_response = "Oups ! Il semble qu'on a rencontré un problème veuillez recharger la page ou réessayer plus tard<br>"
                        return generated_response    
                    try:
                        generated_response = response['choices'][0]['message']['content'].replace('\n', '<br>')
                    except:
                        generated_response = "Oups ! Il semble qu'on a rencontré un problème veuillez réessayer, si le problème persiste veuillez recharger la page ou réessayer plus tard<br>"
                        return generated_response
                    return generated_response
                else:
                    generated_response = "Oups ! Il semble que je n'arrive pas à obtenir des informations, essayez une autre expression.<br>"    
                    return generated_response
            else:
                generated_response = "Oups ! Il semble qu'on a rencontré un problème veuillez réessayer, si le problème persiste veuillez recharger la page ou réessayer plus tard<br>"
                return generated_response       
    elif "False" in response_data.key_word:
        response_data.key_word = response_data.key_word.replace('False', '')
        generated_response = response_data.key_word.replace('\n', '<br>')
        return generated_response
    else:
        generated_response = "Oups ! Il semble que je n'arrive pas à obtenir des informations, essayez une autre expression.<br>"
        return generated_response

# Fonction qui recherche la demande administrative correspondante à partir du message de l'utilisateur
def generate_key_word(user_question, response_data):
    prompt = [{"role": "user", "content": f"""Contexte : Tu es chargé d'identifier le mot clé dans le texte concernant une démarche administrative au Sénégal, dans le cas contraire demander à l'utilisateur de te donner plus d'informations pertinentes en n'hésitant pas à le saluer. 
    NB: Ajoute à la ligne après ta réponse : True  (si mot trouvé) ou False (dans le cas contraire)
    Texte : Je souhaite connaitre la démarche pour obtenir ma carte d'identité.
    Réponse : carte d'identité
    True
    Texte : Bonjour, comment ça va ?
    Réponse : Bonjour, veuillez me fournir des informations précises concernant une demande administrative.
    False
    Texte : Comment récupérer mon diplôme du bac ?
    Réponse : diplôme du baccalauréat 
    True
    Texte : Comment peux-tu m'aider ?
    Réponse : Je pourrai vous aider à obtenir des informations relatives à une démarche administrative au Sénégal de votre choix.
    False
    Texte : {user_question}
    Réponse : 
    """}]
    try:
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = prompt,
        max_tokens=50,
        temperature=0.7
        )
    except openai.error.OpenAIError as e:
        print("erreur openai : ", e.error)
        response_data.key_word = "Oups ! Il semble qu'on a rencontré un problème veuillez réessayer, si le problème persiste veuillez recharger la page ou réessayer plus tard<br>"
        return response_data.key_word
    try:
        response_data.key_word = response['choices'][0]['message']['content']
    except:
        response_data.key_word = "Oups ! Il semble qu'on a rencontré un problème veuillez réessayer, si le problème persiste veuillez recharger la page ou réessayer plus tard<br>"   
        return response_data.key_word 
    return response_data.key_word

# Fonction qui appelle les deux fonctions précédentes pour retourner la réponse finale
def generate_response(user_question, response_data):
    if response_data.first_time:
        response_data.key_word = generate_key_word(user_question, response_data)
        generated_response = search(user_question, response_data)
        response_data.first_time  = False
        return generated_response
    elif response_data.first_time == False and len(response_data.final_data) == 0:
        response_data.key_word = generate_key_word(user_question, response_data)
        generated_response = search(user_question, response_data)
        return generated_response
    else:
        prompt = [{"role": "user", "content": f"""Contexte : Réponds à la demande de l'utilisateur dans le cadre des démarches administratives au Sénégal, en te basant sur les informations suivantes, S'il sagit des remerciements ou une confirmation réponds de manière conviviale et Si tu constates que les informations du site ne permettent pas de répondre à la  question de l'utilisateur réponds juste par le mot "False".
                    informations du site : {response_data.final_data}
                    Utilisateur : {user_question}
                    Réponse : 
                    """}]
        try:
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = prompt,
            max_tokens=800,
            temperature=0.7
            )
        except openai.error.OpenAIError as e:
            print("erreur openai : ", e.error)
            generated_response = "Oups ! Il semble qu'on a rencontré un problème veuillez recharger la page ou réessayer plus tard<br>"
            return generated_response    
        try:
            generated_response = response['choices'][0]['message']['content'].replace('\n', '<br>')
        except:
            generated_response = "Oups ! Il semble qu'on a rencontré un problème veuillez réessayer, si le problème persiste veuillez recharger la page ou réessayer plus tard<br>"
                        
            return generated_response
        if "False" in generated_response:
            response_data.first_time = True
            generated_response = generate_response(user_question, response_data)
            return generated_response
        else: 
            return generated_response               
                
        

        
            
