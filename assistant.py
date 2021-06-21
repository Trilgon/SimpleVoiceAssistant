import webbrowser  # поддержка работы с браузером
from vosk import Model, KaldiRecognizer  # оффлайн-распознавание речи от Vosk
import speech_recognition  # распознавание речи (Speech-To-Text)
import pyttsx3  # синтез речи (Text-To-Speech)
import wave  # создание и чтение аудиофайлов формата wav
import json  # работа с json-файлами и json-строками
import os  # работа с файловой системой

tts_engine = pyttsx3.init()


def setup_assistant_voice():
    voices = tts_engine.getProperty("voices")
    tts_engine.setProperty("voice", "ru")


def play_voice_assistant_speech(text_to_speech):
    """
    Проигрывание речи ответов голосового ассистента (без сохранения аудио)
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    tts_engine.say(str(text_to_speech))
    tts_engine.runAndWait()


def play_greetings(*args: tuple):
    play_voice_assistant_speech("Приветствую")


def play_np(*args: tuple):
    play_voice_assistant_speech("Рада помочь")


def play_goodbye_and_quit(*args: tuple):
    play_voice_assistant_speech("Хорошего вам дня")
    tts_engine.stop()
    quit()


def search_in_google(*args: tuple):
    if not args[0]:
        return
    search_term = " ".join(args[0])
    url = "https://www.google.com/search?q=" + search_term
    webbrowser.get().open(url)

    play_voice_assistant_speech("Вот, что было найдено по запросу " + search_term + " в гугл")


def search_for_video_on_youtube(*args: tuple):
    if not args[0]:
        return
    search_term = " ".join(args[0])
    url = "https://www.youtube.com/results?search_query=" + search_term
    webbrowser.get().open(url)

    play_voice_assistant_speech("Вот, что было найдено по запросу " + search_term + " на youtube")


def search_for_definition_on_wikipedia(*args: tuple):
    if not args[0]:
        return
    search_term = " ".join(args[0])
    url = "https://ru.wikipedia.org/wiki/" + search_term
    webbrowser.get().open(url)

    play_voice_assistant_speech("Вот, что было найдено по запросу " + search_term + " в википедии")


class VoiceAssistant(object):
    name = ""
    speech_language = ""
    tts_engine = None
    recognizer = None
    microphone = None

    def __init__(self, name):
        # инициализация инструментов распознавания и ввода речи
        self.recognizer = speech_recognition.Recognizer()
        self.microphone = speech_recognition.Microphone()

        # настройка данных голосового помощника
        self.name = name
        self.speech_language = "ru"

        # инициализация голоса
        setup_assistant_voice()

    def use_offline_recognition(self):
        recognized_data = ""
        if not os.path.exists("models/vosk-model-small-ru-0.4"):
            print("Please download the model from:\n"
                  "https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
            exit(1)

        # анализ записанного в микрофон аудио (чтобы избежать повторов фразы)
        wave_audio_file = wave.open("microphone-results.wav", "rb")
        model = Model("models/vosk-model-small-ru-0.4")
        offline_recognizer = KaldiRecognizer(model, wave_audio_file.getframerate())

        data = wave_audio_file.readframes(wave_audio_file.getnframes())
        if len(data) > 0:
            if offline_recognizer.AcceptWaveform(data):
                recognized_data = offline_recognizer.Result()

                # получение данных распознанного текста из JSON-строки
                # (чтобы можно было выдать по ней ответ)
                recognized_data = json.loads(recognized_data)
                recognized_data = recognized_data["text"]
        return recognized_data

    def record_and_recognize_audio(self, *args: tuple):
        """
        Запись и распознавание аудио
        """
        with self.microphone:
            recognized_data = ""

            # регулирование уровня окружающего шума
            self.recognizer.adjust_for_ambient_noise(self.microphone, duration=1)

            try:
                print("Listening...")
                audio = self.recognizer.listen(self.microphone, 5, 5)

                with open("microphone-results.wav", "wb") as file:
                    file.write(audio.get_wav_data())

            except speech_recognition.WaitTimeoutError:
                print("Пожалуйста, проверье свой микрофон")
                return

            # использование online-распознавания через Google
            # (высокое качество распознавания)
            try:
                print("Started recognition...")
                # распознование речи Google
                recognized_data = self.recognizer.recognize_google(audio, language="ru").lower()

            except speech_recognition.UnknownValueError:
                pass

            # в случае проблем с доступом в Интернет происходит
            # попытка использовать offline-распознавание через Vosk
            except speech_recognition.RequestError:
                print("Trying to use offline recognition...")
                recognized_data = self.use_offline_recognition()

            return recognized_data

    def start_assistant(self):
        while True:
            # старт записи речи с последующим выводом распознанной речи
            # и удалением записанного в микрофон аудио
            voice_input = self.record_and_recognize_audio()
            os.remove("microphone-results.wav")
            print(voice_input)

            # отделение комманд от дополнительной информации (аргументов)
            voice_input = voice_input.split(" ")
            command = voice_input[0]
            command_options = [str(input_part) for input_part in voice_input[1:len(voice_input)]]
            self.execute_command_with_name(command, command_options)

    def execute_command_with_name(self, command_name: str, *args: list):
        """
        Выполнение заданной пользователем команды с дополнительными аргументами
        :param command_name: название команды
        :param args: аргументы, которые будут переданы в функцию
        :return:
        """
        for key in self.commands.keys():
            if command_name in key:
                self.commands[key](*args)
            else:
                pass

    commands = {
        ("здравствуй", "привет", "доброе", "добрый", "приветствую"): play_greetings,
        ("пока", "выйти", "выключись", "остановись", "прекратить"): play_goodbye_and_quit,
        ("найди", "найти", "поиск", "загугли", "открой"): search_in_google,
        ("смотреть", "видео"): search_for_video_on_youtube,
        ("определение", "википедия", "словарь"): search_for_definition_on_wikipedia,
        ("спасибо", "благодарю", "молодец"): play_np
    }
