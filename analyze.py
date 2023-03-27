import inspect
from inspect import signature
import json

class IspitajObjekat():

    def __init__(self, objekat):
        klase = []
        moduli = []
        metodi = []
        svojstva_property = []
        funkcije = []
        konstante = []
        default = []
        ostalo = []
        argumenti = ""

        tekst = ""
        for att in dir(objekat):
            atribut = str(getattr(objekat,att))
            if att.find("__") >= 0:
                default.append(att)
            elif atribut.find("<class") >= 0 and att.find("__") == -1:
                klase.append(att)
            elif atribut.find("<module") >= 0:
                moduli.append(att)
            elif atribut.find("<method") >= 0:
                metodi.append(att)
            elif atribut.find("<bound method") >= 0:
                metodi.append(att)
            elif atribut.find("<built-in method") >= 0:
                metodi.append(att)
            elif atribut.find("<property") >= 0:
                svojstva_property.append(att)
            elif atribut.find("<function") >= 0:
                funkcije.append(att)
            elif atribut.find("<bound function") >= 0:
                funkcije.append(att)
            elif atribut.find("<built-in function") >= 0:
                funkcije.append(att)
            elif atribut.find("<") == -1:
                konstante.append([att, atribut])
            else:
                ostalo.append(att)

        # Snimanje u fajl
        # Prikupljanje dodatnih informacija
        # Argumenti
        try:
            argspec = inspect.getfullargspec(objekat)
            a = ", ".join(argspec.args)
            if type(a) != str:
                a = ""
        except:
            a = ""
        argumenti = a
        # Docstring
        try:
            doc_string = inspect.getdoc(objekat)
            if type(doc_string) != str:
                doc_string = ""
        except:
            doc_string = ""
        # Izvorni kod
        try:
            source = inspect.getsource(objekat)
        except:
            source = ""
        # Hijerarhija nasledjivanja
        try:
            mro1 = inspect.getmro(object)
            mro2 = [cls.__name__ for cls in mro1]
            mro = ",".join(mro2)
        except:
            mro = ""
        # Ispitivanje da li je ugradjeni Python objekat
        try:
            if inspect.isbuiltin(objekat):
                py_obj = "True"
            else:
                py_obj = "False"
        except:
            py_obj = "Information not available"
        # Naziv fajla u kom se objekat nalazi
        try:
            obj_file_name = inspect.getfile(objekat)
        except:
            obj_file_name = ""
        # Naziv modula u kom se objekat nalazi
        try:
            obj_module = str(inspect.getmodule(objekat))
        except:
            obj_module = ""

        gg = open("result.txt", "w", encoding="utf-8")
        niz = []
        naziv_objekta = objekat.__name__
        niz.append([0, argumenti, naziv_objekta, doc_string, source, mro, py_obj, obj_file_name, obj_module])

        for i in klase:
            niz.append([1, "", i, "", "", "", "", "", ""])
        for i in moduli:
            niz.append([2, "", i, "", "", "", "", "", ""])
        for i in metodi:
            niz.append([3, "", i, "", "", "", "", "", ""])
        for i in svojstva_property:
            niz.append([4, "", i, "", "", "", "", "", ""])
        for i in funkcije:
            niz.append([5, "", i, "", "", "", "", "", ""])
        for i in konstante:
            niz.append([6, i[1], i[0], "", "", "", "", "", ""])
        for i in ostalo:
            niz.append([7, "", i, "", "", "", "", "", ""])

        json.dump(niz, gg)
        gg.close()



class do_it():
    def __init__(self):
        import pygame
        i = IspitajObjekat(pygame)