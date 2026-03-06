#ifndef _TRIOMINO_H_
#define _TRIOMINO_H_

#include <iostream>
#include <list>

template <typename T>
class Tri{
public:
    Tri(T aa, T bb, T cc) : a(aa), b(bb), c(cc) {}

    bool operator==(const Tri& rhs)
    {
        return ((a==rhs.a && b==rhs.b && c==rhs.c) || (c==rhs.a && a==rhs.b && b==rhs.c) || (b==rhs.a && c==rhs.b && a==rhs.c));
    }

    bool canMatch(std::pair<T,T> p)
    {
        return ((b==p.first && a==p.second) || (c==p.first && b==p.second) || (a==p.first && c==p.second));
    }

private:
    T a;
    T b;
    T c;
};

template <typename T>
class triomino{
public:
    bool insert(T a, T b, T c)
    {
        Tri t = Tri(a, b, c);

        std::pair<T,T> p1 = std::make_pair(a, b);
        std::pair<T,T> p2 = std::make_pair(b, c);
        std::pair<T,T> p3 = std::make_pair(c, a);

        if(tabla.size() == 0)
        {
            tabla.push_back(t);
            ends.push_back(p1);
            ends.push_back(p2);
            ends.push_back(p3);

            return true;
        }

        typename std::list<std::pair<T,T> >::iterator it;
        for (it = ends.begin(); it != ends.end(); it++) {
            if(t.canMatch(*it))
            {
                if(it->first==b && it->second==a)
                {
                    ends.push_back(p2);
                    ends.push_back(p3);
                }
                else if(it->first==c && it->second==b)
                {
                    ends.push_back(p1);
                    ends.push_back(p3);
                }
                else if(it->first==a && it->second==c)
                {
                    ends.push_back(p1);
                    ends.push_back(p2);
                }
                else
                {
                    std::cout << "Error: unknown match found" << std::endl;
                    return false;
                }

                tabla.push_back(t);
                ends.erase(it);
                return true;
            }
        }

        return false;
    }

    int size()
    {
        return tabla.size();
    }

    bool contains(T a, T b, T c)
    {
        Tri to = Tri(a,b,c);

        typename std::list<Tri<T> >::iterator it;
        for (it = tabla.begin(); it != tabla.end(); it++)
        {
            if(it->operator==(to))
            {
                return true;
            }
        }

        return false;
    }

private:
    std::list<Tri<T> > tabla;
    std::list<std::pair<T,T> > ends;
};


#endif
