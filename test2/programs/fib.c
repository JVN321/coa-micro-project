#define N 100

int fib[N];

void compute() {
    fib[0] = 0;
    fib[1] = 1;

    for(int i = 2; i < N; i++) {
        fib[i] = fib[i-1] + fib[i-2];
    }
}

int main() {
    compute();
    return 0;
}