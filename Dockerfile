FROM python:latest
WORKDIR /install
RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y git sqlite3 ffmpeg npm
RUN rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m pip install -r requirements.txt --break-system-packages
COPY app/static/package.json .
ENV PATH=$PATH:/usr/local/bin
RUN npm install -g http-server
RUN npm install

WORKDIR /test_data
# Setup Test Environment
RUN wget "https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4.zip" && unzip bbb_sunflower_1080p_30fps_normal.mp4.zip && rm bbb_sunflower_1080p_30fps_normal.mp4.zip
RUN wget "https://tcgplayer-cdn.tcgplayer.com/product/42346_200w.jpg"

RUN mkdir -p /media/raw_files \
    && mkdir -p /media/raw_files/ \
    && mkdir -p /media/library/books \
    && mkdir -p /media/library/movies \
    && mkdir -p /media/library/tv_shows \
    && mkdir -p /media/library/tv_shows/Vampire \
    && mkdir -p /media/library/tv_shows/Werewolf \
    && mkdir -p /media/library/tv_shows/Vans \
    && touch /media/raw_files/editor_metadata.json \
    && mkdir -p /media/library_2/books \
    && mkdir -p /media/library_2/movies \
    && mkdir -p /media/library_2/tv_shows \
    && mkdir -p /media/library_2/tv_shows/Gremlins \
    && mkdir -p /media/library_2/tv_shows/Dinosaurs \
    && mkdir -p /media/library_2/tv_shows/Vans \
    && cp 42346_200w.jpg "/media/library/books/Dinosaur Rawr - another author.mp4.jpg" \
    && cp 42346_200w.jpg "/media/library/movies/Vampire (2020).mp4.jpg" \
    && cp 42346_200w.jpg "/media/library/tv_shows/Vampire/Vampire.jpg" \
    && cp 42346_200w.jpg "/media/library/tv_shows/Vampire/Vampire - s01e001.mp4.jpg" \
    && cp 42346_200w.jpg "/media/library/tv_shows/Vampire/Vampire - s01e001.mp4.jpg" \
    && cp 42346_200w.jpg "/media/library_2/tv_shows/Gremlins/Gremlins.jpg" \
    && cp 42346_200w.jpg "/media/library_2/tv_shows/Gremlins/Gremlins - s01e001.mp4.jpg" \
    && cp 42346_200w.jpg "/media/library_2/tv_shows/Gremlins/Gremlins - s01e001.mp4.jpg" \
    && cp 42346_200w.jpg "/media/library_2/books/Leonard Wears Pajamas - another author.mp4.jpg" \
    && cp 42346_200w.jpg "/media/library_2/movies/Leonard (2018).mp4.jpg" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/raw_files/2024-01-31_16-32-32.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/books/Dinosaur Rawr - another author.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/books/This is a book title - I'm an author.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/movies/Vampire (2020).mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/movies/Vampire 2 (2022).mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/movies/The Cat Returns (2002).mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Vampire/Vampire - s01e001.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Vampire/Vampire - s01e002.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Vampire/Vampire - s02e1.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Vampire/Vampire - s02e2.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Vampire/Vampire - s02e3.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Werewolf/Werewolf - s01e001.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Werewolf/Werewolf - s01e2.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Werewolf/Werewolf - s01e3.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Werewolf/Werewolf - s02e002.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Werewolf/Werewolf - s03e1.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Vans/Vans - s02e001.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library/tv_shows/Vans/Vans - s02e2.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/books/Leonard Wears Pajamas - another author.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/books/Leonard Drives A Bus - I'm an author.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/movies/Leonard (2018).mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/movies/Leonard 2 (2019).mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/movies/Leonard Plays Dressup (2002).mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Gremlins/Gremlins - s01e001.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Gremlins/Gremlins - s01e002.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Gremlins/Gremlins - s02e1.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Gremlins/Gremlins - s02e2.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Gremlins/Gremlins - s02e3.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Dinosaurs/Dinosaurs - s01e001.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Dinosaurs/Dinosaurs - s01e2.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Dinosaurs/Dinosaurs - s01e3.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Dinosaurs/Dinosaurs - s02e002.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Dinosaurs/Dinosaurs - s03e1.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Vans/Vans - s02e003.mp4" \
    && ln -s /test_data/bbb_sunflower_1080p_30fps_normal.mp4 "/media/library_2/tv_shows/Vans/Vans - s1e1.mp4"

WORKDIR /app
RUN git config --global --add safe.directory /app
#COPY . .
#RUN npm install --prefix app/static
#CMD ["python", "run.py"]
