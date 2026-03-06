#include <iostream>
#include "triomino.h"
#include <string>
#include <cctype>
#include "triomino.h"

struct case_insensitive
{
  bool operator()( char a, char b ) const
  {
    return std::tolower( a ) == std::tolower( b );
  }
};

const int max = 1000;

int main()
{
  int your_mark = 1;
  // 2-es // 35 perc
  triomino<int> a;
  a.insert( 0, 1, 2 );
  a.insert( 5, 2, 1 );
  a.insert( 1, 3, 5 );
  a.insert( 4, 2, 5 );

  for( int i = 0; i < max; ++i )
  {
    a.insert( 5, 5, 5 );
  }

  triomino<std::string> s;
  s.insert( "C++", "Rust", "Fortran" );
  s.insert( "Go", "Fortran", "Rust" );

  if( !a.insert( 1, 6, 2 ) && !s.insert( "Java", "C#", "C#" ) && 4 == a.size() )
  {
    your_mark = s.size();
  }
  
  // 3-as // 7 perc
  s.insert( "Ada", "Rust", "C++" );
  if( s.contains( "Rust", "Fortran", "C++" ) && !s.contains( "C", "C", "C" ) &&
      !a.contains( 5, 5, 5 ) && a.contains( 5, 4, 2 ) && a.contains( 0, 1, 2 ) )
  {
    your_mark = s.size();
  }
  
  // 4-es
  triomino<int> b;
  b.insert( 1, 3, 4 );
  b.insert( 1, 5, 3 );

  triomino<int> c;
  c.insert( 3, 4, 1 );
  c.insert( 5, 3, 1 );

  triomino<std::string> t;
  t.insert( "C", "D", "Eiffel" );

  if ( c.equals( b ) && !a.equals( b ) && c == b && !( t == s ) )
  {
    your_mark = b.size() + c.size();
  }
  
  /* 5-os
  triomino<char, case_insensitive> ch;
  ch.insert( 'A', 'B', 'C' );
  ch.insert( 'S', 'b', 'a' );
  if( 2 == ch.size() )
  {
    your_mark += ch.contains( 'A', 'S', 'B' );
  }
  */
  std::cout << "Your mark is " << your_mark << std::endl;
}
