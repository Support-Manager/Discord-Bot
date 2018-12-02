from bot.models import Ticket
from .embed_paginator import EmbedPaginator
from .embed_constructors import ticket_embed, response_embed


class TicketViewer(EmbedPaginator):
    """ Represents an interactive menu containing the whole data of a ticket (including responses). """

    def __init__(self, ctx, ticket: Ticket):
        pages = [ticket_embed(ctx, ticket)]
        response_embeds = \
            [response_embed(ctx, r) for r in sorted(ticket.get_responses(), key=lambda r: r.id)]

        pages.extend(response_embeds)

        super().__init__(ctx, pages)
