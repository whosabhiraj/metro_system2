import random
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from ticket.models import Station, Line, Ticket

class line():
    def __init__(self, name, station_ids):
        self.name = name
        self.station_ids = station_ids

class station():
    def __init__(self, name, id):
        self.name = name
        self.id = id

class ticket():
    def __init__(self, id, start_station, end_station, price):
        self.id = id
        self.start_station = start_station
        self.end_station = end_station
        self.price = price


class metro_system():
    def __init__(self):
        self.stations = self.load_stations()
        

    def load_stations(self):
        stations = []
        # using django table instead of csv
        db_stations = Station.objects.all()
        
        for s in db_stations:
            stations.append(station(s.name, str(s.id)))

        return stations
    

    def load_lines(self):
        lines = {}
        db_lines = Line.objects.all()

        for l in db_lines:
            name = l.name
            stations_on_line = l.stations_online.split(';')
            lines[name] = stations_on_line

        return lines
    
    
    def load_tickets(self):
        tickets = {}
        db_tickets = Ticket.objects.all()

        for t in db_tickets:
            ticket_id = t.id
            start_name = t.start_station
            end_name = t.end_station
            price = str(t.price) # retain csv behaviour as reading csv used to output str
            tickets[ticket_id] = [ticket_id, start_name, end_name, price]
            
        return tickets


    def display_stations(self):
        print("Available Stations:")
        for station in self.stations:
            print(f"Station {station.name} is available.")
        print("---------------------------")
        

    def display_lines(self):
        lines = self.load_lines()
        print("Available Lines:")
        for line, stations in lines.items():
            print(f"Line {line} with stations: {', '.join(stations)}")
        print("---------------------------")


    def display_tickets(self, ticket):
        print("---------------------------")
        print(f"Ticket ID: {ticket.id}")
        print(f"From: {ticket.start_station} \n To: {ticket.end_station}")
        print(f"Price: {ticket.price}")
        print("---------------------------")


    def generate_ticket(self, start_name, end_name):
        path = self.pathfind(start_name, end_name)
        price = 10
        length = path.index(end_name) - path.index(start_name) # type: ignore
        uid = str(random.randint(100000, 999999))

        ticket_new = ticket(uid, start_name, end_name, price*length)
        self.display_tickets(ticket_new)
        
        return ticket_new

    
    def generate_graph(self, lines_dict):
        graph = {}

        for line in lines_dict:
            stations = lines_dict[line]
            for i in range(len(stations) - 1):
                a = stations[i].strip().lower()
                b = stations[i + 1].strip().lower()

                if a not in graph:
                    graph[a] = []
                if b not in graph:
                    graph[b] = []

                graph[a].append(b)
                graph[b].append(a)
        # print(graph)
        return graph


    def pathfind(self, start_name, end_name):
        graph = self.generate_graph(self.load_lines())
        visited = []
        queue = [[start_name]]

        while len(queue) > 0:
            path = queue.pop(0)
            node = path[-1]

            if node == end_name:
                return(path)

            if node not in visited:
                visited.append(node)
                for adjacent in graph.get(node, []): # ??????
                    new_path = list(path)
                    new_path.append(adjacent)
                    queue.append(new_path)


    def ticket_viewer(self, mode): 
        tickets = self.load_tickets()
        
        if len(tickets) == 0:
            print("No tickets found.")
            print("---------------------------")
            return

        if mode == "1":
            uid = input("Enter your ticket ID: ").strip()
            if uid in tickets:
                self.display_tickets(ticket(*tickets.get(uid))) # type: ignore
            else:
                print("Ticket not found.")

        elif mode == "2":
            for uid in tickets:
                self.display_tickets(ticket(*tickets.get(uid))) # type: ignore

        else:
            print("Invalid input.")
            print("---------------------------")


    def cli(self):
        while True:
            print("1. View Stations")
            print("2. View Lines")
            print("3. View Tickets")
            print("4. Purchase Ticket")
            print("5. Exit")
            choice = input("Enter your choice: ")
            print("---------------------------")

            if choice == '1':
                self.display_stations()

            elif choice == '2':
                self.display_lines()

            elif choice == '3':
                self.ticket_viewer(input("Enter 1 for a specific ticket or 2 for all tickets: ").strip())

            elif choice == '4':
                print("Enter starting station name: ")
                start_name = input().strip().lower()
                print("Enter ending station name: ")
                end_name = input().strip().lower()
                self.generate_ticket(start_name, end_name)

            elif choice == '5':
                print("Exiting.")
                print("***************************")
                break

            else:
                print("Invalid choice. Please try again.")
                print("---------------------------")

if __name__ == "__main__":
    metro_system().cli()