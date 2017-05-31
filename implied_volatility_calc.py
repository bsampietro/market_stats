from scipy.stats import norm
import math

norm.cdf(1.96)
#c_p - Call(+1) or Put(-1) option
#P - Price of option

# Bruno: one of this is stock price, and the other one is strikeprice
#    To calculate the whole IV, one should use the same value ??
#S - Strike price
#E - Exercise price -- Bruno: I think this is strike price

#T - Time to expiration
#r - Risk-free rate

#C = SN(d_1) - Ee^{-rT}N(D_2)


def implied_volatility(Price,Stock,Exercise,Time,Rf):
    P = float(Price)
    S = float(Stock)
    E = float(Exercise)
    T = float(Time)
    r = float(Rf)
    sigma = 0.01
    print (P, S, E, T, r)
    while sigma < 1:
        d_1 = float(float((math.log(S/E)+(r+(sigma**2)/2)*T))/float((sigma*(math.sqrt(T)))))
        d_2 = float(float((math.log(S/E)+(r-(sigma**2)/2)*T))/float((sigma*(math.sqrt(T)))))
        P_implied = float(S*norm.cdf(d_1) - E*math.exp(-r*T)*norm.cdf(d_2))
        if P-(P_implied) < 0.001:
            return sigma
        sigma +=0.001
    return "could not find the right volatility"

print(implied_volatility(15,100,100,1,0.05))

print(implied_volatility(480,240,240,24,0.50))