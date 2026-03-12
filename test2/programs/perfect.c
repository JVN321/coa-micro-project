#define N 200

int A[N];
int B[N];

void compute() {

    B[0] = A[0];

    for(int i=1;i<N;i++) {
        B[i] = B[i-1] + A[i];
    }

}

int main() {
    compute();
    return 0;
}