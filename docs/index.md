# Desktop App to Process Insole Sensor Data
## Team Members: 
 - Chase Davis
 - John Halpin
 - Nathan Rings
 - Ryan Macfarlane

## Project Abstract
Boise State University COBR (Center For Orthopedic & Biomechanics Research) has no method of visualizing the data collected from their XSensor insole measurement device. The goal of this project is to create an interactive and convenient solution for data visualization that can be easily utilized and customized. Our sponsor needed a way to process the data they got from the XSensor (an insole device that has an array of sensors used for gait and motion research) after testing sessions so they could look at and calculate specific things they were looking for depending on the test they ran. For example, if they did a test where they had the test subject jump in place wearing the XSensor insole they might want to be able to take the data captured during the test to see things like the amount of pressure being exerted from the subjects dominate foot compared to their non-dominate foot. With this application they will be able to do that and more with a variety of different calculations and visualizations of given data and can export the processed data. Another reason that our sponsor wanted an application like this is to be able to freely share it to other researchers so that others can use the same application that our sponsor’s lab used to calculate the data they obtained to verify their findings and for others to build upon this application for different purposes.

## Project Description
Using Python we built a desktop application that takes in a CSV data file produced by the XSensor insole device and processes it into different visualizations and calculations of the data. The user can import a CSV file that will be parsed to create a data table and perform all the visualizations and starting calculations that will be displayed in different tabs in our application. The Data Table tab displays the created table along with fields the user can use to input extra information. In the Visualization tab the user can select what metric they want visualized as a graph and can choose the frame range and whether to show the left foot, right foot, or both in the graph. The Calculations tab allows the user to look at visualizations of different calculations done on the data while also being able to adjust the frame window of what range of calculations to visualize from. This tab also has a menu that lets the user see and adjust the different calculations and can compute new calculations and save or delete any calculations that have been performed. In the Session Summary tab there is a summary of the data the was processed and provides different stats about the current session. There is also an Export feature that allows the user to export any of the visualizations, calculations, and data table to different types of formats.

![Github](https://github.com/user-attachments/assets/ef9ae9db-ae64-437d-b45e-60e3347c2024)
![Github](https://github.com/user-attachments/assets/4b7d5094-5434-4362-bba8-02044d7f5237)
![Github](https://github.com/user-attachments/assets/99130b66-ff03-42db-9dd1-ea90a8b8a0d2)
<img width="616" height="835" alt="image" src="https://github.com/user-attachments/assets/bbefa8d6-1b06-4c32-8228-961db4e8f0bc" />
