# Hospitals_Dijkstras
Our project aims to build a simple route optimization system to the nearest hospitals using Dijkstra’s Algorithm. The application gets the longitude and latitude of all hospitals in the US and narrows it down from a user specified location. The program will first narrow down the data by checking for keywords (state, city, zip code, etc.) Dijkstra’s algorithm will be used to then find the shortest path from the current location. We will use Python to implement the algorithm and optionally visualize the result using NetworkX or Matplotlib. 

### Dataset Download
#### https://www.kaggle.com/datasets/andrewmvd/us-hospital-locations/data
- Download Dataset from link
- Specify Relative Path to file in HospitalApp,py

### Necessary Dependencies Download
- Download requirements.txt
    ```bash
    pip install -r requirements.txt
    ```

### Running Program
- Once dependencies are installed, run dijkstras_algorithm,py
    ```bash
    python dijkstras_algorithm.py
    ```