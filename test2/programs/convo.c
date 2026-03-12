#define N 100

int input[N];
int kernel[3] = {1,2,1};
int output[N];

void compute() {

    for(int i=1;i<N-1;i++) {
        output[i] =
            input[i-1]*kernel[0] +
            input[i]*kernel[1] +
            input[i+1]*kernel[2];
    }

}

int main() {
    compute();
    return 0;
}