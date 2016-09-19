from microsofttranslator import Translator
from apiclient.discovery import build

input_file = open("input.txt", "r").readlines()
google_output_file = open("google_output.txt", "w")
microsoft_output_file = open("microsoft_output.txt", "w")

google_portuguese_list = []
google_english_list = []
microsoft_portuguese_list = []
microsoft_english_list = []

def main():
    #start translators
    google_translator = build('translate', 'v2', developerKey='')
    microsoft_translator = Translator('', '')


    #Google
    google_response1 = google_translator.translations().list(
      source='en',
      target='pt',
      q=input_file
    ).execute()

    for x in google_response1["translations"]:
        google_portuguese_list.append(x["translatedText"])

    google_response2 = google_translator.translations().list(
      source='pt',
      target='en',
      q=google_portuguese_list
    ).execute()

    for x in google_response2["translations"]:
        #google_english_list.append(x["translatedText"])
        google_output_file.write(x["translatedText"] + "\n")


    #Microsoft
    microsoft_response1 = microsoft_translator.translate_array(input_file, 'pt')
    for x in microsoft_response1:
        #print x["TranslatedText"]
        microsoft_portuguese_list.append(x["TranslatedText"].strip())    

    microsoft_response2 = microsoft_translator.translate_array(microsoft_portuguese_list, 'en')
    for x in microsoft_response2:
        #print x["TranslatedText"]
        #microsoft_english_list.append(x["TranslatedText"])
        print x["TranslatedText"]
        microsoft_output_file.write(x["TranslatedText"].strip() + "\n")

    
if __name__ == '__main__':
    main()
    google_output_file.close()
    microsoft_output_file.close()

    file1 = open("google_output.txt").readlines()
    file2 = open("microsoft_output.txt").readlines()
    file3 = open("google_microsoft_output.txt", "w")
    file3.write("Original\tGooglePT\tMicrosoftPT\tGoogleEN\tMicrosoftEN\n")

    for i in range(len(file1)):
        file3.write(input_file[i].strip() + "\t" + microsoft_portuguese_list[i].strip().encode('utf8') + "\t" +  google_portuguese_list[i].strip().encode('utf8') + "\t" + file1[i].strip() + "\t" + file2[i].strip() + "\n")

    file3.close()
