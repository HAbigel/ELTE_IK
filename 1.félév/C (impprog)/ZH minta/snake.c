#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#DIM1 10
#DIM2 20



int main()
{
	int s;
	int o;
	srand(time(NULL));
	char tomb[DIM1][DIM2]; // \0 ?
	for(int i=0; i<10; ++i)
	{
		s = rand()%10;
		o = rand()%20;
		while(tomb[s][o] == 'a')
		{
			s = rand()%10;
			o = rand()%20;
		}
		tomb[s][o] = 'a';
	}
	
	return 0;
}