import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(5),
            max_tickets = sp.nat(5),
            operator = sp.test_account("admin").address,
        )
    
    @sp.entry_point
    def buy_ticket(self, num_tickets):

        sp.set_type(num_tickets, sp.TNat)

        # Sanity checks
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(self.data.tickets_available >= num_tickets, "TOO MANY REQUESTED TICKETS, THERE ARE NOT ENOUGH TICKETS AVAILABLE")
        sp.verify(sp.amount >= sp.mul(self.data.ticket_cost, num_tickets), "INVALID AMOUNT")

        # Storage updates
        sp.for i in sp.range(0, num_tickets, step = 1):
            self.data.players[sp.len(self.data.players)] = sp.sender
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - num_tickets)

        # Return extra tez balance to the sender
        extra_balance = sp.amount - sp.mul(self.data.ticket_cost, num_tickets)
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")

        # Pick a winner
        winner_id = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_price(self, new_price):

        sp.set_type(new_price, sp.TNat)

        # Sancheck
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "GAME IS ONGOING, FAILED TO CHANGE PRICE")

        # Update ticket price
        self.data.ticket_cost = sp.utils.nat_to_mutez(new_price)

    @sp.entry_point
    def change_ticket_count(self, new_max_count):
        sp.set_type(new_max_count, sp.TNat)

        # Sancheck
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "GAME IS ONGOING, FAILED TO CHANGE TIX COUNT")

        # Update ticket price
        self.data.max_tickets = new_max_count
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def default(self):
        sp.failwith("NOT ALLOWED")

@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")
    charles = sp.test_account("charles")
    john = sp.test_account("john")

    # Contract instance
    lottery = Lottery()
    scenario += lottery

    # buy_ticket
    scenario.h2("buy_ticket (valid single tickets test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = bob)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(3), sender = john)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = charles)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = mike)

    scenario.h2("end_game (valid single test)")
    scenario += lottery.end_game(21).run(sender = admin)

    scenario.h2 ("change price and number of tickets (valid test)")
    scenario += lottery.change_price(2000000).run(sender = admin)
    scenario += lottery.change_ticket_count(20).run(sender = admin)

    scenario.h2("buy_ticket (valid multiple tickets test)")
    scenario += lottery.buy_ticket(5).run(amount = sp.tez(12), sender = alice)
    scenario += lottery.buy_ticket(4).run(amount = sp.tez(80), sender = bob)
    scenario += lottery.buy_ticket(5).run(amount = sp.tez(10), sender = john)
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(6), sender = charles)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = mike)

    scenario.h2 ("change price (invalid test)")
    scenario += lottery.change_price(2000000).run(sender = admin, valid = False)

    scenario.h2 ("change ticket count (invalid test)")
    scenario += lottery.change_ticket_count(20).run(sender = admin, valid = False)

    scenario.h2("buy_ticket (lacking funds test)")
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(1), sender = alice, valid = False)

    scenario.h2("buy_ticket (buying too much test)")
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(6), sender = alice, valid = False)

    scenario.h2("end_game (invalid test)")
    scenario += lottery.end_game(22).run(sender = admin, valid = False)

    scenario.h2("buy_ticket (filling in missing ticket to enable end_game)")
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(4), sender = alice)

    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(22).run(sender = admin)
