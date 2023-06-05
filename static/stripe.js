const express = require('express')
const Stripe = require('stripe')
const { Order } = require('../models/order')

require('dotenv').config()

const stripe = Stripe(process.env.STRIPE_KEY)

const router = express.Router()

router.post('/create-checkout-session', async (req, res) => {
  const customer = await stripe.customers.create({
    metadata: {
      userId: req.body.userId
    }
  })

  const line_items = req.body.cartItems.map(item => ({
    price_data: {
      currency: 'usd',
      product_data: {
        name: item.name,
        images: [item.image.url],
        description: item.desc,
        metadata: { id: item.id }
      },
      unit_amount: item.price * 100
    },
    quantity: item.cartQuantity
  }))

  const session = await stripe.checkout.sessions.create({
    shipping_address_collection: { allowed_countries: ['US', 'CA', 'KZ'] },
    shipping_options: [
      {
        shipping_rate_data: {
          type: 'fixed_amount',
          fixed_amount: { amount: 0, currency: 'usd' },
          display_name: 'Free shipping',
          delivery_estimate: {
            minimum: { unit: 'business_day', value: 5 },
            maximum: { unit: 'business_day', value: 7 }
          }
        }
      }
    ],
    phone_number_collection: {
      enabled: true
    },
    customer: customer.id,
    line_items,
    mode: 'payment',
    success_url: `${process.env.CLIENT_URL}/checkout-success`,
    cancel_url: `${process.env.CLIENT_URL}/cart`
  })
  res.send({ url: session.url })
})

const createOrder = async (customer, data, lineItems) => {
  const newOrder = new Order({
    userId: customer.metadata.userId,
    customerId: data.customer,
    paymentIntentId: data.payment_intent,
    products: lineItems.data,
    subtotal: data.amount_subtotal,
    total: data.amount_total,
    shipping: data.customer_details,
    payment_status: data.payment_status
  })

  try {
    const savedOrder = await newOrder.save()
    console.log('Processed Order:', savedOrder)
  } catch (err) {
    console.log(err)
  }
}

// This is your Stripe CLI webhook secret for testing your endpoint locally.
let endpointSecret
// endpointSecret = 'whsec_ebf84400f8b55d46906b472c78446a729b8679680faa5a77f0f7dea739858506'

router.post(
  '/webhook',
  express.raw({ type: 'application/json' }),
  (request, response) => {
    const sig = request.headers['stripe-signature']

    let data, eventType

    if (endpointSecret) {
      let event

      try {
        event = stripe.webhooks.constructEvent(
          request.body,
          sig,
          endpointSecret
        )
        console.log('Webhook verified.')
      } catch (err) {
        console.log(`Webhook Error: ${err.message}`)
        response.status(400).send(`Webhook Error: ${err.message}`)
        return
      }

      data = event.data.object
      eventType = event.type
    } else {
      data = request.body.data.object
      eventType = request.body.type
    }

    if (eventType === 'checkout.session.completed')
      stripe.customers
        .retrieve(data.customer)
        .then(customer => {
          stripe.checkout.sessions.listLineItems(
            data.id,
            {},
            function (err, lineItems) {
              console.log('line_items', lineItems)

              createOrder(customer, data, lineItems)
            }
          )
        })
        .catch(err => console.log(err.message))

    // Return a 200 response to acknowledge receipt of the event
    response.send().end()
  }
)

module.exports = router
