# Learn SDN
Repositori berisikan beragam referensi, dokumentasi, contoh program, slide belajar dan mengajar untuk software-defined networking (SDN). Isi dari repositori akan terus diperbaharui.

## Getting started
Untuk memulai cukup lakukan duplikasi repositori ini melalui perintah git
```bash
 git clone https://github.com/abazh/learn_sdn
```
Selanjutnya, cek ke masing-masing direktori untuk dokumentasi spesifik.
- [Server Load Balancing](LB)
- [Shortest Path First Routing](SPF)

Proses running
Buka 3 container 
1. Container1  --> docker compose up -d #untuk membangun docker container yang berjalan di background  
2. Container2  --> docker exec -it learn_sdn bash
               --> osken-manager --observe-links dijkstra_osken_controller.py
3. Container3  --> docker exec -it learn_sdn bash
               --> python3 dijkstra_osken_controller.py