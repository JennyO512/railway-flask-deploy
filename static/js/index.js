const express = require('express')
const cors = require('cors')
const mongoose = require('mongoose')
const products = require('./products')
const register = require('./routes/register')
const login = require('./routes/login')
const stripe = require('./routes/stripe')
const productsRoute = require('./routes/products')
const users = require('./routes/users')
const orders = require('./routes/orders')

const app = express()

require('dotenv').config()

app.use(express.json())
app.use(cors())

app.use('/api/register', register)
app.use('/api/login', login)
app.use('/api/stripe', stripe)
app.use('/api/products', productsRoute)
app.use('/api/users', users)
app.use('/api/orders', orders)

app.get('/', (_, res) => res.send('Welcome to our online shop API...'))
app.get('/products', (_, res) => res.send(products))

const port = process.env.PORT || 5000
const uri = process.env.DB_URI

app.listen(port, console.log(`Server running on port ${port}`))

mongoose.set('strictQuery', false)
mongoose
  .connect(uri)
  .then(() => console.log('MongoDB connection successful...'))
  .catch(err => console.log('MongoDB connection failed', err.message))