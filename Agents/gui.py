import tkinter as tk

def retrieve_data():
    # Inizializziamo una lista per contenere i risultati (per aggirare lo scope)
    risultati = []

    root = tk.Tk()
    root.title("Data Insertion")
    root.geometry("600x400")

    def send_data():
        # Salviamo i dati nella lista esterna
        risultati.append(entry_logger.get())
        risultati.append(entry_friend1.get())
        risultati.append(entry_friend2.get())
        risultati.append(entry_rounds.get())
        risultati.append(entry_graph.get())
        # Chiudiamo la finestra per sbloccare l'esecuzione e arrivare al return
        root.destroy()

    tk.Label(root, text="Logger's Name:").pack(pady=5)
    entry_logger = tk.Entry(root)
    entry_logger.pack(pady=5)

    tk.Label(root, text="Bob's Friends:").pack(pady=5)
    entry_friend1 = tk.Entry(root)
    entry_friend1.pack(pady=5)

    tk.Label(root, text="Frank's Friends:").pack(pady=5)
    entry_friend2 = tk.Entry(root)
    entry_friend2.pack(pady=5)

    tk.Label(root, text="Nr of rounds:").pack(pady=5)
    entry_rounds = tk.Entry(root)
    entry_rounds.pack(pady=5)

    tk.Label(root, text="Graph Name:").pack(pady=5)
    entry_graph = tk.Entry(root)
    entry_graph.pack(pady=5)

    btn_send = tk.Button(root, text="send", command=send_data)
    btn_send.pack(pady=20)

    root.mainloop()

    # Se la lista è vuota (es. finestra chiusa con la X), evitiamo errori di unpacking
    if not risultati:
        return None, None, None, None
        
    return risultati[0], risultati[1], risultati[2], risultati[3], risultati[4]

def retrieve_person():
    # Inizializziamo una lista per contenere i risultati (per aggirare lo scope)
    risultati = []

    root = tk.Tk()
    root.title("Explore the graph")
    root.geometry("600x400")

    def choose_person():
        # Salviamo i dati nella lista esterna
        risultati.append(entry_person.get())
        # Chiudiamo la finestra per sbloccare l'esecuzione e arrivare al return
        root.destroy()

    tk.Label(root, text="Choose a Node:").pack(pady=5)
    entry_person = tk.Entry(root)
    entry_person.pack(pady=5)

    btn_send = tk.Button(root, text="send", command=choose_person)
    btn_send.pack(pady=20)

    root.mainloop()

    # Se la lista è vuota (es. finestra chiusa con la X), evitiamo errori di unpacking
    if not risultati:
        return None
        
    return risultati[0]


# Esempio di chiamata
if __name__=="__main__":
    logger, f1, f2, rounds = retrieve_data()
    print(f"Dati ottenuti: {logger}, {f1}, {f2}, {rounds}")

