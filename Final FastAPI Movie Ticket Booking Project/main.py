from math import ceil
from typing import Optional

from fastapi import FastAPI, Query, Response, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Movie Ticket Booking API")


# sample movie data
movies = [
    {
        "id": 1,
        "title": "Sky Force",
        "genre": "Action",
        "language": "Hindi",
        "duration_mins": 145,
        "ticket_price": 220,
        "seats_available": 50,
    },
    {
        "id": 2,
        "title": "Laugh Riot",
        "genre": "Comedy",
        "language": "English",
        "duration_mins": 120,
        "ticket_price": 180,
        "seats_available": 40,
    },
    {
        "id": 3,
        "title": "Midnight Fear",
        "genre": "Horror",
        "language": "Hindi",
        "duration_mins": 110,
        "ticket_price": 200,
        "seats_available": 35,
    },
    {
        "id": 4,
        "title": "Broken Strings",
        "genre": "Drama",
        "language": "English",
        "duration_mins": 135,
        "ticket_price": 160,
        "seats_available": 60,
    },
    {
        "id": 5,
        "title": "Mission Zero",
        "genre": "Action",
        "language": "Tamil",
        "duration_mins": 150,
        "ticket_price": 250,
        "seats_available": 45,
    },
    {
        "id": 6,
        "title": "Ghost House",
        "genre": "Horror",
        "language": "Telugu",
        "duration_mins": 125,
        "ticket_price": 190,
        "seats_available": 30,
    },
]

bookings = []
booking_id_counter = 1

holds = []
hold_id_counter = 1


class BookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=10)
    phone: str = Field(..., min_length=10)
    seat_type: str = Field(default="standard", min_length=3)


class MovieCreate(BaseModel):
    title: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=2)
    language: str = Field(..., min_length=2)
    duration_mins: int = Field(..., gt=0)
    ticket_price: int = Field(..., gt=0)
    seats_available: int = Field(..., ge=0)


class HoldRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=10)


def get_movie(movie_id: int):
    for movie in movies:
        if movie["id"] == movie_id:
            return movie
    return None


def ticket_cost(price: int, seats: int, seat_type: str):
    seat_type = seat_type.lower()

    if seat_type == "premium":
        multiplier = 1.5
    elif seat_type == "recliner":
        multiplier = 2
    else:
        multiplier = 1

    return price * seats * multiplier


def filter_movie_list(movie_list, genre=None, language=None, max_price=None):
    result = movie_list

    if genre:
        result = [m for m in result if m["genre"].lower() == genre.lower()]

    if language:
        result = [m for m in result if m["language"].lower() == language.lower()]

    if max_price is not None:
        result = [m for m in result if m["ticket_price"] <= max_price]

    return result


def search_movie_list(movie_list, keyword=None):
    if not keyword:
        return movie_list

    keyword = keyword.lower()
    return [
        m for m in movie_list
        if keyword in m["title"].lower()
        or keyword in m["genre"].lower()
        or keyword in m["language"].lower()
    ]


def sort_movie_list(movie_list, sort_by="ticket_price", order="asc"):
    allowed_fields = ["ticket_price", "title", "duration_mins"]

    if sort_by not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort_by. Use ticket_price, title or duration_mins"
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid order. Use asc or desc"
        )

    return sorted(movie_list, key=lambda x: x[sort_by], reverse=(order == "desc"))


def paginate_data(data, page, limit):
    total = len(data)
    total_pages = ceil(total / limit) if total > 0 else 1

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "items": data[start:end]
    }


@app.get("/")
def home():
    return {"message": "Welcome to Movie Ticket Booking API"}


@app.get("/movies")
def get_all_movies():
    return {
        "total_movies": len(movies),
        "movies": movies
    }


@app.get("/bookings")
def get_all_bookings():
    total_revenue = sum(b["total_price"] for b in bookings)
    return {
        "total_bookings": len(bookings),
        "total_revenue": total_revenue,
        "bookings": bookings
    }


@app.get("/movies/summary")
def movie_summary():
    genre_data = {}

    for movie in movies:
        genre = movie["genre"]
        genre_data[genre] = genre_data.get(genre, 0) + 1

    prices = [m["ticket_price"] for m in movies]
    seats = [m["seats_available"] for m in movies]

    return {
        "total_movies": len(movies),
        "highest_ticket_price": max(prices) if prices else 0,
        "lowest_ticket_price": min(prices) if prices else 0,
        "total_seats": sum(seats),
        "movies_by_genre": genre_data
    }


@app.get("/movies/filter")
def filter_movies(
    genre: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    max_price: Optional[int] = Query(default=None, gt=0)
):
    result = filter_movie_list(movies, genre, language, max_price)
    return {
        "count": len(result),
        "movies": result
    }


@app.post("/movies")
def add_movie(movie: MovieCreate, response: Response):
    for m in movies:
        if m["title"].lower() == movie.title.lower():
            raise HTTPException(status_code=400, detail="Movie already exists")

    new_id = max([m["id"] for m in movies], default=0) + 1

    new_movie = {
        "id": new_id,
        "title": movie.title,
        "genre": movie.genre,
        "language": movie.language,
        "duration_mins": movie.duration_mins,
        "ticket_price": movie.ticket_price,
        "seats_available": movie.seats_available
    }

    movies.append(new_movie)
    response.status_code = 201
    return new_movie


@app.post("/bookings")
def create_booking(data: BookingRequest, response: Response):
    global booking_id_counter

    movie = get_movie(data.movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    if data.seat_type.lower() not in ["standard", "premium", "recliner"]:
        raise HTTPException(
            status_code=400,
            detail="Seat type must be standard, premium or recliner"
        )

    if movie["seats_available"] < data.seats:
        raise HTTPException(status_code=400, detail="Not enough seats available")

    total_price = ticket_cost(movie["ticket_price"], data.seats, data.seat_type)
    movie["seats_available"] -= data.seats

    booking = {
        "booking_id": booking_id_counter,
        "customer_name": data.customer_name,
        "movie_id": data.movie_id,
        "movie_title": movie["title"],
        "phone": data.phone,
        "seats": data.seats,
        "seat_type": data.seat_type,
        "total_price": total_price,
        "status": "confirmed"
    }

    bookings.append(booking)
    booking_id_counter += 1
    response.status_code = 201
    return booking


@app.post("/seat-hold")
def create_hold(data: HoldRequest, response: Response):
    global hold_id_counter

    movie = get_movie(data.movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie["seats_available"] < data.seats:
        raise HTTPException(status_code=400, detail="Not enough seats available")

    movie["seats_available"] -= data.seats

    hold = {
        "hold_id": hold_id_counter,
        "customer_name": data.customer_name,
        "movie_id": data.movie_id,
        "movie_title": movie["title"],
        "seats": data.seats,
        "status": "held"
    }

    holds.append(hold)
    hold_id_counter += 1
    response.status_code = 201
    return hold


@app.get("/seat-hold")
def get_holds():
    return {
        "total_holds": len(holds),
        "holds": holds
    }


@app.post("/seat-confirm/{hold_id}")
def confirm_hold(hold_id: int, response: Response):
    global booking_id_counter

    selected_hold = None
    for h in holds:
        if h["hold_id"] == hold_id:
            selected_hold = h
            break

    if selected_hold is None:
        raise HTTPException(status_code=404, detail="Hold not found")

    movie = get_movie(selected_hold["movie_id"])
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    total_price = ticket_cost(movie["ticket_price"], selected_hold["seats"], "standard")

    booking = {
        "booking_id": booking_id_counter,
        "customer_name": selected_hold["customer_name"],
        "movie_id": selected_hold["movie_id"],
        "movie_title": movie["title"],
        "phone": "Not Provided",
        "seats": selected_hold["seats"],
        "seat_type": "standard",
        "total_price": total_price,
        "status": "confirmed_from_hold"
    }

    bookings.append(booking)
    holds.remove(selected_hold)
    booking_id_counter += 1
    response.status_code = 201

    return {
        "message": "Seat hold confirmed",
        "booking": booking
    }


@app.delete("/seat-release/{hold_id}")
def release_hold(hold_id: int):
    selected_hold = None
    for h in holds:
        if h["hold_id"] == hold_id:
            selected_hold = h
            break

    if selected_hold is None:
        raise HTTPException(status_code=404, detail="Hold not found")

    movie = get_movie(selected_hold["movie_id"])
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie["seats_available"] += selected_hold["seats"]
    holds.remove(selected_hold)

    return {
        "message": "Seat hold released",
        "hold_id": hold_id
    }


@app.get("/movies/search")
def search_movies(keyword: str = Query(..., min_length=1)):
    result = search_movie_list(movies, keyword)
    return {
        "keyword": keyword,
        "count": len(result),
        "movies": result
    }


@app.get("/movies/sort")
def sort_movies(
    sort_by: str = Query(default="ticket_price"),
    order: str = Query(default="asc")
):
    result = sort_movie_list(movies, sort_by, order)
    return {
        "sort_by": sort_by,
        "order": order,
        "movies": result
    }


@app.get("/movies/page")
def get_movies_page(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=3, ge=1, le=10)
):
    return paginate_data(movies, page, limit)


@app.get("/bookings/search")
def search_bookings(customer_name: str = Query(..., min_length=1)):
    result = [
        b for b in bookings
        if customer_name.lower() in b["customer_name"].lower()
    ]
    return {
        "customer_name": customer_name,
        "count": len(result),
        "bookings": result
    }


@app.get("/bookings/sort")
def sort_bookings(order: str = Query(default="asc")):
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    result = sorted(bookings, key=lambda x: x["total_price"], reverse=(order == "desc"))
    return {
        "order": order,
        "bookings": result
    }


@app.get("/movies/browse")
def browse_movies(
    keyword: Optional[str] = Query(default=None),
    sort_by: str = Query(default="ticket_price"),
    order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=4, ge=1, le=10)
):
    result = search_movie_list(movies, keyword)
    result = sort_movie_list(result, sort_by, order)
    paginated = paginate_data(result, page, limit)

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": paginated["page"],
        "limit": paginated["limit"],
        "total": paginated["total"],
        "total_pages": paginated["total_pages"],
        "movies": paginated["items"]
    }


@app.put("/movies/{movie_id}")
def update_movie(
    movie_id: int,
    ticket_price: Optional[int] = Query(default=None, gt=0),
    seats_available: Optional[int] = Query(default=None, ge=0)
):
    movie = get_movie(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    if ticket_price is not None:
        movie["ticket_price"] = ticket_price

    if seats_available is not None:
        movie["seats_available"] = seats_available

    return {
        "message": "Movie updated successfully",
        "movie": movie
    }


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    movie = get_movie(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    for booking in bookings:
        if booking["movie_id"] == movie_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete movie because bookings already exist"
            )

    movies.remove(movie)
    return {
        "message": "Movie deleted successfully",
        "deleted_movie": movie["title"]
    }


@app.get("/movies/{movie_id}")
def get_movie_by_id(movie_id: int):
    movie = get_movie(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie